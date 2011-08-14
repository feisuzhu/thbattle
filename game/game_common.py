import logging
from gevent import Timeout

log = logging.getLogger('Game')

class TimeLimitExceeded(Timeout):
    pass

class GameError(Exception):
    pass

class EventHandler(object):

    def handle(self, evt_type, act):
        raise GameError('Override handle function to implement EventHandler logics!')

    def interested(self, evt_type, act):
        raise GameError('Override this!')

class Action(object):
    cancelled = False
    default_action = False
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

class DataHolder(object):
    def __data__(self):
        return self.__dict__

class Player(object):

    def __data__(self):
        d = User.__data__(self)
        d.update(
            dummy='dummy',
        )
        return d

class Game(object):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    event_handlers = []
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
        if isinstance(data, object):
            s = data.__class__.__name__
        else:
            s = data
        log.info('emit_event: %s %s' % (evt_type, s))
        for evt in self.event_handlers:
            if evt.interested(evt_type, data):
                data = evt.handle(evt_type, data)
        return data

    def process_action(self, action):
        '''
        Process an action
        '''
        if action.can_fire():
            action.set_up()
            action = self.emit_event('action_before', action)
            if action.can_fire() and not action.cancelled:
                log.info('applying action %s' % action.__class__.__name__)
                try:
                    if self.SERVER_SIDE and action.default_action:
                        with TimeLimitExceeded(30):
                            rst = action.apply_action()
                    else:
                        rst = action.apply_action()
                except TimeLimitExceeded:
                    log.info('action timeout, use default_action: %s' % action.__class__.__name__)
                    rst = action.default_action()

                assert rst in [True, False], 'Action.apply_action or default_action  must return boolean!'
            else:
                return False
            action = self.emit_event('action_after', action)
            action.clean_up()
            return rst
        else:
            return False
