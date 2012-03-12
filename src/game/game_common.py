import logging
from gevent import Timeout
from utils import DataHolder

log = logging.getLogger('Game')

class TimeLimitExceeded(Timeout):
    pass

class GameError(Exception):
    pass

class GameEnded(Exception):
    pass

class EventHandler(object):

    def handle(self, evt_type, data):
        raise GameError('Override handle function to implement EventHandler logics!')

class Action(object):
    cancelled = False
    def __init__(self):
        pass

    def can_fire(self):
        '''
        Return true if the action can be fired.
        '''
        return self.game_class.getgame().emit_event('action_can_fire', self)

    def apply_action(self):
        raise GameError('Override apply_action to implement Action logics!')

    def set_up(self):
        '''
        Execute before 'action_before' event
        '''
        pass

    def clean_up(self):
        '''
        Execute after all event handlers finished there work.
        '''
        pass

    def cancel(self, cancel=True):
        self.cancelled = cancel

class AbstractPlayer(object):
    def reveal(self, obj_list):
        raise GameError('Abstract')

    def user_input(self, tag, attachment=None, timeout=25):
        raise GameError('Abstract')

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

    def game_start(self):
        '''
        Game logic goes here.
        GameModes should override this.
        '''
        raise GameError('Override this function to implement Game logics!')

    def game_ended(self):
        raise GameError('Override this')

    def emit_event(self, evt_type, data):
        '''
        Fire an event, all relevant event handlers will see this,
        data can be modified.
        '''
        if isinstance(data, object):
            s = data.__class__.__name__
        else:
            s = data
        log.info('emit_event: %s %s' % (evt_type, s))
        for evt in self.event_handlers:
            data = evt.handle(evt_type, data)
        return data

    @staticmethod
    def getgame():
        raise GameError('Abstract')

    def process_action(self, action):
        '''
        Process an action
        '''
        if action.can_fire():
            action.set_up()
            action = self.emit_event('action_before', action)
            if not action.cancelled and action.can_fire():
                log.info('applying action %s' % action.__class__.__name__)
                    #, src=%d, dst=%d' % (
                    #action.__class__.__name__,
                    #self.players.index(action.source) if hasattr(action, 'source') else -1,
                    #self.players.index(action.target),
                #))
                action = self.emit_event('action_apply', action)

                rst = action.apply_action()

                assert rst in [True, False], 'Action.apply_action must return boolean!'
                action.succeeded = rst
                if self.game_ended():
                    raise GameEnded()
                action = self.emit_event('action_after', action)
            else:
                log.info('action cancelled/invalid %s' % action.__class__.__name__)
                return False

            action.clean_up()
            return rst
        else:
            return False

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

    def get_syncid(self):
        raise GameError('Abstract')

class SyncPrimitive(object):
    def __init__(self, value):
        self.value = value

    def sync(self, data):
        self.value = self.value.__class__(data)

    def __data__(self):
        return self.value
