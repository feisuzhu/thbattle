import gevent
from gevent import Greenlet, Timeout
from gevent.queue import Queue
from user import User

class GameError(Exception):
    pass

class TimeLimitExceeded(Timeout):
    pass

class EventHandler(object):
    def __init__(self):
        self.handles = None # here should be a subclass of Action

    def handle(self, evt_type, act):
        raise GameError('Override handle function to implement EventHandler logics!')

    def interested(self, evt_type, act):
        raise GameError('Override this!')

class Action(object):
    def __init__(self):
        pass

    def can_fire(self):
        '''
        Return true if the action can be fired.
        '''
        return Game.get_current().emit_event('action_can_fire', self)
    
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

class DataHolder(object):
    def __data__(self):
        return self.__dict__

class Player(User):

    def __data__(self):
        d = User.__data__(self)
        d.update(
            dummy='dummy',
        )
        return d

class DroppedPlayer(Player):
    
    def write(self, data):
        pass

    def read(self):
        return ['dropped_player']

class Game(Greenlet):
    '''
    The Game class, all game mode derives from this.
    Provides fundamental behaviors.

    Instance variables:
        players: list(Players)
        event_handlers: list(EventHandler)

        and all game related vars, eg. tags used by [EventHandler]s and [Action]s
    '''
    player_class = Player

    def __data__(self):
        return dict(
            id=id(self),
            type=self.__class__.name,
            empty_slots=self.__class__.n_persons - len(self.players),
        )
    def __init__(self):
        Greenlet.__init__(self)
        self.players = []
        self.queue = Queue(100)

    def _run(self):
        for u in self.players:
            u.__class__ = self.__class__.player_class
            u.active_queue = None
            u.gamedata = DataHolder()

        self.game_start()
        # game ended
        for p in self.players:
            del p.gamedata
            p.__class__ = User
            p.active_queue = p.receptionist.wait_channel

        from server.core import gamehall as hall
        hall.end_game(self)

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
            if action.can_fire():
                action.apply_action()
            else:
                return False
            action = self.emit_event('action_after', action)
            action.clean_up()
            return True
        else:
            return False

    @staticmethod
    def get_current():
        '''
        Return current game object
        '''
        return gevent.getcurrent().thisgame

    def init(self):
        '''
        Greenlet entrypoint
        '''
        c = gevent.getcurrent()
        c.thisgame = self
        self.start()


    



    
