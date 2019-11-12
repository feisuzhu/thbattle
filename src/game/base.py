# -*- coding: utf-8 -*-
from __future__ import absolute_import

# -- stdlib --
from collections import defaultdict, deque
from contextlib import contextmanager
import logging
import random

# -- third party --
from gevent import Timeout, getcurrent
from gevent.event import Event
import gevent

# -- own --
from endpoint import EndpointDied
from utils import Packet, exceptions, instantiate


# -- code --
log = logging.getLogger('Game')

intern('action_shootdown')
intern('action_before')
intern('action_apply')
intern('action_after')

all_gameobjects = set()
game_objects_hierarchy = set()


class GameObjectMeta(type):
    def __new__(mcls, clsname, bases, _dict):
        for k, v in _dict.items():
            if isinstance(v, (list, set)):
                _dict[k] = tuple(v)  # mutable obj not allowed

        cls = type.__new__(mcls, clsname, bases, _dict)
        all_gameobjects.add(cls)
        for b in bases:
            game_objects_hierarchy.add((b, cls))

        return cls

    def __getattribute__(cls, name):
        value = type.__getattribute__(cls, name)
        if isinstance(value, classmethod):
            try:
                rep_class = cls.rep_class(cls)
                return lambda *a, **k: value.__get__(None, rep_class)
            except:
                pass

        return value

    @staticmethod
    def _dump_gameobject_hierarchy():
        with open('/dev/shm/gomap.dot', 'w') as f:
            f.write('digraph {\nrankdir=LR;\n')
            f.write('\n'.join([
                '"%s" -> "%s";' % (a.__name__, b.__name__)
                for a, b in game_objects_hierarchy
            ]))
            f.write('}')

    # def __setattr__(cls, field, v):
    #     type.__setattr__(cls, field, v)
    #     if field in ('ui_meta', ):
    #         return
    #
    #     log.warning('SetAttr: %s.%s = %s' % (cls.__name__, field, repr(v)))


class GameObject(object):
    __metaclass__ = GameObjectMeta


class TimeLimitExceeded(Timeout):
    __metaclass__ = GameObjectMeta


class GameException(Exception):
    __metaclass__ = GameObjectMeta

    def __init__(self, msg=None, **kwargs):
        Exception.__init__(self, msg)
        self.__dict__.update(kwargs)


class GameError(GameException):
    pass


class GameEnded(GameException):
    pass


class InterruptActionFlow(GameException):
    def __init__(self, unwind_to=None):
        GameException.__init__(self)
        self.unwind_to = unwind_to


class ActionShootdown(BaseException):
    __metaclass__ = GameObjectMeta

    def __nonzero__(self):
        return False


class EventHandler(GameObject):
    execute_before = ()
    execute_after = ()
    group = None
    interested = None

    def handle(self, evt_type, data):
        raise GameError('Override handle function to implement EventHandler logics!')

    def get_interested(self):
        interested = self.interested
        assert isinstance(interested, (list, tuple)), "Should specify interested events! %r" % self.__class__
        return list(interested)

    @staticmethod
    def make_list(eh_classes, fold_group=True):
        table = {}
        eh_classes = set(eh_classes)
        groups = defaultdict(list)

        for cls in eh_classes:
            assert not issubclass(cls, EventHandlerGroup), 'Should not pass group in make_list, %r' % cls
            grp = cls.group if fold_group else None
            if grp is not None:
                groups[grp].append(cls)
                cls = grp

            table[cls.__name__] = cls()

        for grp, lst in groups.iteritems():
            eh = table[grp.__name__]
            eh.set_handlers(EventHandler.make_list(lst, fold_group=False))

        allnames = frozenset(table)

        for eh in table.itervalues():
            eh.execute_before = set(eh.execute_before) & allnames  # make it instance var
            eh.execute_after = set(eh.execute_after) & allnames

        for clsname, eh in table.iteritems():
            for before in eh.execute_before:
                table[before].execute_after.add(clsname)

            for after in eh.execute_after:
                table[after].execute_before.add(clsname)

        l = table.values()
        l.sort(key=lambda v: v.__class__.__name__)  # must sync between server and client

        toposorted = []
        while l:
            deferred = []
            commit = []
            for eh in l:
                if not eh.execute_after:
                    for b in eh.execute_before:
                        table[b].execute_after.remove(eh.__class__.__name__)
                    commit.append(eh)
                else:
                    deferred.append(eh)

            if not commit:
                raise GameError("Can't resolve dependencies! Check for circular reference!")

            toposorted.extend(commit)
            l = deferred

        return toposorted

    @staticmethod
    def _dump_eh_dependency_graph():
        from game.autoenv import EventHandler
        ehs = {i for i in all_gameobjects if issubclass(i, EventHandler)}
        ehs.remove(EventHandler)
        dependencies = set()
        for eh in ehs:
            for b in eh.execute_before:
                dependencies.add((eh.__name__, b))

            for a in eh.execute_after:
                dependencies.add((a, eh.__name__))

        with open('/dev/shm/eh_relations.dot', 'w') as f:
            f.write('digraph {\nrankdir=LR;\n')
            f.write('\n'.join([
                '%s -> %s;' % (a, b)
                for a, b in dependencies
            ]))
            f.write('}')


class EventHandlerGroup(EventHandler):
    handlers = ()

    def set_handlers(self, handlers):
        self.handlers = handlers[:]


class Action(GameObject):
    cancelled = False
    done = False
    invalid = False

    def __new__(cls, *a, **k):
        try:
            g = Game.getgame()
            actual_cls = g.action_types.get(cls, cls)
        except:
            g = None
            actual_cls = cls

        obj = GameObject.__new__(actual_cls, *a, **k)

        if g:
            for hook in reversed(g._action_hooks):
                obj = hook(obj)

        return obj

    @staticmethod
    def rep_class(cls):
        try:
            g = Game.getgame()
            return g.action_types.get(cls, cls)
        except:
            return cls

    def __init__(self, source, target):
        self.source = source
        self.target = target

    def action_shootdown_exception(self):
        if not self.is_valid():
            raise ActionShootdown(self)

        _ = Game.getgame().emit_event('action_shootdown', self)
        assert _ is self, "You can't replace action in 'action_shootdown' event!"

    def action_shootdown(self):
        try:
            self.action_shootdown_exception()
            return None

        except ActionShootdown as e:
            return e

    def can_fire(self):
        '''
        Return true if the action can be fired.
        '''
        rst = self.action_shootdown()
        return True if rst is None else rst

    def apply_action(self):
        raise GameError('Override apply_action to implement Action logics!')

    def is_valid(self):
        '''
        Return True if this action is complete and ready to fire.
        '''
        return True

    def __repr__(self):
        return self.__class__.__name__


class AbstractPlayer(GameObject):
    index = None

    def reveal(self, obj_list):
        raise GameError('Abstract')

    def __repr__(self):
        return self.__class__.__name__


class NPC(object):
    __slots__ = ('name', 'input_handler')

    def __init__(self, name, input_handler):
        self.name = name
        self.input_handler = input_handler


class Game(GameObject):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)
        npc_players: list(NPC)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    # event_handlers = []
    IS_DEBUG = False
    params_def = {}
    npc_players = []

    def __init__(self):
        self.event_handlers = []
        self.adhoc_ehs      = []
        self.ehs_cache      = {}
        self.action_stack   = []
        self.hybrid_stack   = []
        self.action_types   = {}
        self.ended          = False
        self._action_hooks  = []
        self.winners        = []
        self.turn_count     = 0
        self.event_observer = None

    def set_event_handlers(self, ehs):
        self.event_handlers = ehs[:]
        self.ehs_cache = {}
        self.adhoc_ehs = []

    def add_adhoc_event_handler(self, eh):
        self.adhoc_ehs.insert(0, eh)

    def remove_adhoc_event_handler(self, eh):
        try:
            self.adhoc_ehs.remove(eh)
        except ValueError:
            pass

    def players_from(g, p):
        if p is None:
            id = 0
        elif p in g.players:
            id = g.get_playerid(p)
        else:
            id = p.index

        n = len(g.players)

        for i in range(id, n) + range(id):
            yield g.players[i]

    def game_end(self):
        self.ended = True
        try:
            winner = self.winners[0].identity
        except:
            winner = None

        log.info(u'>> Winner: %s', winner)
        gevent.sleep(2)

        raise GameEnded

    def _get_relevant_eh(self, tag):
        ehs = self.ehs_cache.get(tag)
        if ehs is not None:
            return ehs

        ehs = [
            eh for eh in self.event_handlers if
            tag in eh.get_interested()
        ]
        self.ehs_cache[tag] = ehs

        return ehs

    def emit_event(self, evt_type, data):
        '''
        Fire an event, all relevant event handlers will see this,
        data can be modified.
        '''
        random.random() < 0.01 and gevent.sleep(0.00001)  # prevent buggy logic code blocking scheduling
        if isinstance(data, (list, tuple, str, unicode)):
            s = data
        else:
            s = data.__class__.__name__
        log.debug('emit_event: %s %s' % (evt_type, s))

        if evt_type in ('action_before', 'action_apply', 'action_after'):
            action_event = True
            assert isinstance(data, Action)
        else:
            action_event = False

        ob = self.event_observer
        if ob:
            data = ob.handle(evt_type, data)

        adhoc = self.adhoc_ehs
        ehs = self._get_relevant_eh(evt_type)

        for l in adhoc, ehs:
            for eh in l:
                data = self.handle_single_event(eh, evt_type, data)
                if action_event and data.cancelled:
                    break

        return data

    def handle_single_event(self, eh, *a, **k):
        try:
            self.hybrid_stack.append(eh)
            data = eh.handle(*a, **k)
        finally:
            assert eh is self.hybrid_stack.pop()

        if data is None:
            log.debug('EventHandler %s returned None' % eh.__class__.__name__)

        return data

    @staticmethod
    def getgame():
        from .autoenv import Game
        return Game.getgame()

    def process_action(self, action):
        '''
        Process an action
        '''
        if self.ended:
            return False

        if action.done:
            log.debug('action already done %s' % action.__class__.__name__)
            return action.succeeded
        elif action.cancelled or action.invalid:
            log.debug('action cancelled/invalid %s' % action.__class__.__name__)
            return False

        if not action.can_fire():
            log.debug('action invalid %s' % action.__class__.__name__)
            return False

        try:
            action.succeeded = False
        except AttributeError:
            pass

        action = self.emit_event('action_before', action)
        if action.done:
            log.debug('action already done %s' % action.__class__.__name__)
            rst = action.succeeded
        elif action.cancelled:
            log.debug('action cancelled, not firing: %s' % action.__class__.__name__)
            rst = False
        elif not action.can_fire():
            log.debug('action invalid, not firing: %s' % action.__class__.__name__)
            action.invalid = True
        else:
            log.debug('applying action %s, current hybrid_stack: %r' % (action.__class__.__name__, self.hybrid_stack))
            action = self.emit_event('action_apply', action)
            assert not action.cancelled
            try:
                self.action_stack.append(action)
                self.hybrid_stack.append(action)
                rst = action.apply_action()
            except InterruptActionFlow as e:
                if e.unwind_to is action:
                    rst = False
                else:
                    raise
            finally:
                _a = self.action_stack.pop()
                _b = self.hybrid_stack.pop()
                assert _a is _b is action

                # If exception occurs here,
                # the action should be abandoned,
                # code below makes no sense,
                # so it's ok to ignore them.

            assert rst in [True, False], 'Action.apply_action must return boolean!'
            try:
                action.succeeded = rst
            except AttributeError:
                pass

            action = self.emit_event('action_after', action)

            rst = action.succeeded
            action.done = True

        self.emit_event('action_done', action)

        return rst

    def get_playerid(self, p):
        return self.players.index(p)
        try:
            return self.players.index(p)
        except ValueError:
            return None

    def player_fromid(self, pid):
        return self.players[pid]
        try:
            return self.players[pid]
        except IndexError:
            return None

    def get_synctag(self):
        raise GameError('Abstract')

    @contextmanager
    def action_hook(self, hook):
        ''' Dark art, do not use '''
        try:
            self._action_hooks.append(hook)
            yield
        finally:
            expected_hook = self._action_hooks.pop()
            assert expected_hook is hook


class SyncPrimitive(GameObject):
    def __init__(self, value):
        self.value = value

    def sync(self, data):
        self.value = self.value.__class__(data)

    def __data__(self):
        return self.value

    def __repr__(self):
        return self.value.__repr__()


def sync_primitive(val, to):
    if not to:  # sync to nobody
        return val

    if isinstance(val, list):
        l = [SyncPrimitive(i) for i in val]
        to.reveal(l)
        return val.__class__(
            i.value for i in l
        )
    else:
        v = SyncPrimitive(val)
        to.reveal(v)
        return v.value


def get_seed_for(p):
    from game.autoenv import Game
    if Game.SERVER_SIDE:
        seed = Game.getgame().random.getrandbits(63)
    else:
        seed = 0L

    return sync_primitive(seed, p)


def list_shuffle(lst, plain_to):
    seed = get_seed_for(plain_to)

    if seed:  # cardlist owner & server
        shuffler = random.Random(seed)
        shuffler.shuffle(lst)
    else:  # others
        for i in lst:
            i.conceal()


class Inputlet(GameObject):
    RETRY = object()
    '''
    NOTICE: Inputlet instance variable should
            not be used as side channel for infomation
            passing in game logic code.
    '''
    def __init__(self, initiator, *args, **kwargs):
        self.initiator = initiator
        self.init(*args, **kwargs)

    @classmethod
    def tag(cls):
        clsname = cls.__name__
        assert clsname.endswith('Inputlet')
        return clsname[:-8]

    def init(self):
        pass

    def parse(self, data):
        '''
        Process parsed data, return result,
        return value of this func will be the return value
        of user_input func.
        '''
        return None

    def post_process(self, actor, args):
        '''
        This method is called after self.parse succeeded,
        so game logic may have chance to transform (and validate)
        input result before input process finishes.
        '''
        return args

    def with_post_process(self, f):
        '''
        Helper method, to make this possible
        @ilet.with_post_process
        def process(args):
            ...
        '''
        self.post_process = f
        return f

    def data(self):
        '''
        Encode self, used for reconstrcting
        inputlet state from the other end.
        Will be fed into self.process() of the other end.
        '''
        return None

    def __repr__(self):
        return '<I:{}>'.format(self.tag())


class InputTransaction(object):
    def __init__(self, name, involved, **kwargs):
        self.name = name
        self.involved = involved[:]
        self.__dict__.update(kwargs)

    def __enter__(self):
        return self.begin()

    def begin(self):
        from game.autoenv import Game
        g = Game.getgame()
        g.emit_event('user_input_transaction_begin', self)
        return self

    def __exit__(self, *excinfo):
        self.end()
        return False

    def end(self):
        from game.autoenv import Game
        g = Game.getgame()
        g.emit_event('user_input_transaction_end', self)

    def notify(self, evt_name, arg):
        '''
        Event For UI
        '''
        Game.getgame().emit_event('user_input_transaction_feedback', (self, evt_name, arg))

    def __repr__(self):
        return '<T:{}>'.format(self.name)


class Gamedata(object):
    @instantiate
    class NODATA(object):
        def __repr__(self):
            return 'NODATA'

    def __init__(self, recording=False):
        self.gdqueue = deque(maxlen=100000)
        self.gdevent = Event()
        self.gdempty = Event()
        self.recording = recording
        self.history = []
        self._in_gexpect = False
        self.gdempty.set()

    def feed(self, data):
        p = Packet(data)
        self.gdqueue.append(p)
        self.gdevent.set()
        self.gdempty.clear()

    def gexpect(self, tag, blocking=True):
        try:
            assert not self._in_gexpect, 'NOT REENTRANT'
            self._in_gexpect = True
            blocking and log.debug('GAME_EXPECT: %s', repr(tag))
            l = self.gdqueue
            e = self.gdevent
            ee = self.gdempty
            e.clear()

            glob = False
            if tag.endswith('*'):
                tag = tag[:-1]
                glob = True

            while True:
                for i, packet in enumerate(l):
                    if isinstance(packet, EndpointDied):
                        raise packet

                    if packet[0] == tag or (glob and packet[0].startswith(tag)):
                        log.debug('GAME_READ: %s', repr(packet))
                        del l[i]
                        self.recording and self.history.append(packet)
                        return packet

                    else:
                        log.debug('GAME_DATA_MISS: %s', repr(packet))
                        log.debug('EXPECTS: %s, GAME: %s', tag, getcurrent())

                ee.set()
                if blocking:
                    e.wait(timeout=5)
                    e.clear()
                else:
                    e.clear()
                    return None, self.NODATA
        finally:
            self._in_gexpect = False

    def wait_empty(self):
        self.gdempty.wait()

    def gbreak(self):
        # is it a hack?
        # XXX: definitly, and why it's here?! can't remember
        # Explanation:
        # Well, when sb. exit game in input state,
        # the others must wait until his timeout exceeded.
        # called by lobby.exit_game to break such condition.
        self.gdqueue.append(EndpointDied())
        self.gdevent.set()


class GameItem(object):
    inventory = {}

    key  = None
    args = []
    usable = False

    title = u'ITEM-TITLE'
    description = u'ITEM-DESC'

    def __init__(self, sku, *args):
        self.sku = sku
        self.init(*args)

    def init(self, *args):
        pass

    @classmethod
    def register(cls, item_cls):
        assert issubclass(item_cls, cls)
        cls.inventory[item_cls.key] = item_cls
        return item_cls

    @classmethod
    def from_sku(cls, sku):
        if ':' in sku:
            key, args = sku.split(':')
            args = args.split(',')
        else:
            key = sku
            args = []

        if key not in cls.inventory:
            raise exceptions.InvalidItemSKU

        cls = cls.inventory[key]
        if len(cls.args) != len(args):
            raise exceptions.InvalidItemSKU

        try:
            args = [T(v) for T, v in zip(cls.args, args)]
        except Exception:
            raise exceptions.InvalidItemSKU

        return cls(sku, *args)
