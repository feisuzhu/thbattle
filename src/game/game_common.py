import logging
from gevent import Timeout
from utils import DataHolder
from contextlib import contextmanager

log = logging.getLogger('Game')

intern('action_can_fire')
intern('action_before')
intern('action_apply')
intern('action_after')


class TimeLimitExceeded(Timeout):
    pass


class GameException(Exception):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class GameError(GameException):
    pass


class GameEnded(GameException):
    pass


class InterruptActionFlow(GameException):
    pass


class EventHandler(object):
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
            eh.execute_before = set(eh.execute_before) & allnames # make it instance var
            eh.execute_after = set(eh.execute_after) & allnames
            table[cls.__name__] = eh

        for clsname in table:
            eh = table[clsname]
            for before in eh.execute_before:
                table[before].execute_after.add(clsname)

            for after in eh.execute_after:
                table[after].execute_before.add(clsname)

        l = table.values()
        l.sort(key=lambda v: v.__class__.__name__) # must sync between server and client

        toposorted = []
        while l:
            deferred = []
            commit = []
            added = False
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


class Action(object):
    cancelled = False
    done = False
    _interrupt_after_me = False

    def __new__(cls, *a, **k):
        try:
            g = cls.game_class.getgame()
            actual_cls = g.action_types.get(cls, cls)
        except:
            g = None
            actual_cls = cls

        obj = object.__new__(actual_cls, *a, **k)

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
        _self, rst = self.game_class.getgame().emit_event('action_can_fire', (self, self.is_valid()))
        assert _self is self, "You can't replace action in 'action_can_fire' event!"
        return rst

    def apply_action(self):
        raise GameError('Override apply_action to implement Action logics!')

    def is_valid(self):
        '''
        Return True if this action is complete and ready to fire.
        '''
        return True

    def interrupt_after_me(self):
        self._interrupt_after_me = True

    def __repr__(self):
        return self.__class__.__name__


class AbstractPlayer(object):
    def reveal(self, obj_list):
        raise GameError('Abstract')

    def user_input(self, tag, attachment=None, timeout=15):
        raise GameError('Abstract')

    def __repr__(self):
        return self.__class__.__name__


class Game(object):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    # event_handlers = []
    def __init__(self):
        self.event_handlers = []
        self.action_stack = []
        self.action_types = {}
        self._action_hooks = []

    def game_start(self):
        '''
        Game logic goes here.
        GameModes should override this.
        '''
        raise GameError('Override this function to implement Game logics!')

    def emit_event(self, evt_type, data):
        '''
        Fire an event, all relevant event handlers will see this,
        data can be modified.
        '''
        if isinstance(data, (list, tuple, str, unicode)):
            s = data
        else:
            s = data.__class__.__name__
        log.debug('emit_event: %s %s' % (evt_type, s))
        for evt in self.event_handlers:
            data = evt.handle(evt_type, data)
            if data is None:
                log.debug('EventHandler %s returned None' % evt.__class__.__name__)
        return data

    @staticmethod
    def getgame():
        raise GameError('Abstract')

    def process_action(self, action):
        '''
        Process an action
        '''

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
                rst = action.apply_action()
            finally:
                _a = self.action_stack.pop()
                assert _a is action

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

            if action._interrupt_after_me:
                raise InterruptActionFlow

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
    

class SyncPrimitive(object):
    def __init__(self, value):
        self.value = value

    def sync(self, data):
        self.value = self.value.__class__(data)

    def __data__(self):
        return self.value


def sync_primitive(val, to):
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
