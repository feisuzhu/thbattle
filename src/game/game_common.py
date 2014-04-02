# -*- coding: utf-8 -*-

import logging
import gevent
import random
from gevent import Timeout
from contextlib import contextmanager

log = logging.getLogger('Game')

intern('action_can_fire')
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
    pass


class EventHandler(GameObject):
    execute_before = tuple()
    execute_after = tuple()

    def handle(self, evt_type, data):
        raise GameError('Override handle function to implement EventHandler logics!')

    @staticmethod
    def make_list(eh_classes):
        table = {}

        before_all = []
        after_all = []
        rest = []

        eh_classes = set(eh_classes)
        for cls in eh_classes:
            if cls.execute_before == '__all__':
                before_all.append(cls())
                assert not cls.execute_after
            elif cls.execute_after == '__all__':
                after_all.append(cls())
                assert not cls.execute_before
            else:
                rest.append(cls)

        allnames = set(cls.__name__ for cls in eh_classes)

        for cls in rest:
            eh = cls()
            eh.execute_before = set(eh.execute_before) & allnames  # make it instance var
            eh.execute_after = set(eh.execute_after) & allnames
            table[cls.__name__] = eh

        for clsname in table:
            eh = table[clsname]
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

        rst = before_all + toposorted + after_all

        assert len(rst) == len(eh_classes)

        return rst

    @staticmethod
    def _dump_eh_dependency_graph():
        from game.autoenv import EventHandler
        ehs = set([i for i in all_gameobjects if issubclass(i, EventHandler)])
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


class Action(GameObject):
    cancelled = False
    done = False

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

    def __init__(self, source, target):
        self.source = source
        self.target = target

    def can_fire(self):
        '''
        Return true if the action can be fired.
        '''
        _self, rst = Game.getgame().emit_event('action_can_fire', (self, self.is_valid()))
        assert _self is self, "You can't replace action in 'action_can_fire' event!"
        return rst

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
    def reveal(self, obj_list):
        raise GameError('Abstract')

    def __repr__(self):
        return self.__class__.__name__


class Game(GameObject):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    # event_handlers = []
    IS_DEBUG = False

    def __init__(self):
        self.event_handlers = []
        self.action_stack = []
        self.hybrid_stack = []
        self.action_types = {}
        self.ended = False
        self._action_hooks = []
        self.winners = []
        self.turn_count = 0

    def game_start(self):
        '''
        Game logic goes here.
        GameModes should override this.
        '''
        raise GameError('Override this function to implement Game logics!')

    def game_end(self):
        self.ended = True
        try:
            winner = self.winners[0].identity
        except:
            winner = None

        log.info(u'>> Winner: %s', winner)

        raise GameEnded

    def emit_event(self, evt_type, data):
        '''
        Fire an event, all relevant event handlers will see this,
        data can be modified.
        '''
        random.random() < 0.01 and gevent.sleep(0)  # prevent buggy logic code blocking scheduling
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

        for evt in self.event_handlers:
            try:
                self.hybrid_stack.append(evt)
                data = evt.handle(evt_type, data)
            finally:
                assert evt is self.hybrid_stack.pop()

            if data is None:
                log.debug('EventHandler %s returned None' % evt.__class__.__name__)

            if action_event and data.cancelled:
                break

        return data

    @staticmethod
    def getgame():
        from .autoenv import Game
        return Game.getgame()

    def process_action(self, action):
        '''
        Process an action
        '''
        if self.ended: return False

        if action.done:
            log.debug('action already done %s' % action.__class__.__name__)
            return action.succeeded
        elif action.cancelled:
            log.debug('action cancelled/invalid %s' % action.__class__.__name__)
            return False

        if not action.can_fire():
            log.debug('action invalid %s' % action.__class__.__name__)
            return False

        action = self.emit_event('action_before', action)
        if action.done:
            log.debug('action already done %s' % action.__class__.__name__)
            rst = action.succeeded
        elif action.cancelled or not action.can_fire():
            log.debug('action cancelled/invalid %s' % action.__class__.__name__)
            rst = False
        else:
            log.debug('applying action %s' % action.__class__.__name__)
                #, src=%d, dst=%d' % (
                #action.__class__.__name__,
                #self.players.index(action.source) if hasattr(action, 'source') else -1,
                #self.players.index(action.target),
            #))
            action = self.emit_event('action_apply', action)
            assert not action.cancelled
            try:
                self.action_stack.append(action)
                self.hybrid_stack.append(action)
                rst = action.apply_action()
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
