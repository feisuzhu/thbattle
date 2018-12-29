# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from collections import defaultdict
from random import Random
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Set, TYPE_CHECKING, Tuple, Type
from typing import TypeVar, Union
import logging
import random

# -- third party --
from gevent import Timeout
from gevent.event import Event
from mypy_extensions import TypedDict
import gevent

# -- own --
from endpoint import EndpointDied
from utils.misc import BatchList, exceptions
from utils.viral import ViralContext

# -- typing --
if TYPE_CHECKING:
    from server.base import Game as ServerGame  # noqa: F401
    from server.endpoint import Client  # noqa: F401


# -- code --
log = logging.getLogger('Game')

all_gameobjects = set()
game_objects_hierarchy = set()


class GameObjectMeta(type):
    def __new__(mcls, clsname, bases, kw):
        for k, v in kw.items():
            if isinstance(v, (list, set)):
                kw[k] = tuple(v)  # mutable obj not allowed

        cls = super().__new__(mcls, clsname, bases, kw)
        all_gameobjects.add(cls)
        for b in bases:
            game_objects_hierarchy.add((b, cls))

        return cls

    '''
    def __getattribute__(cls, name):
        value = type.__getattribute__(cls, name)
        if isinstance(value, classmethod):
            try:
                rep_class = cls.rep_class(cls)
                return lambda *a, **k: value.__get__(None, rep_class)
            except Exception:
                pass

        return value
    '''

    @staticmethod
    def _dump_gameobject_hierarchy():
        with open('/dev/shm/gomap.dot', 'w') as f:
            f.write('digraph {\nrankdir=LR;\n')
            f.write('\n'.join([
                '"%s" -> "%s";' % (a.__name__, b.__name__)
                for a, b in game_objects_hierarchy
            ]))
            f.write('}')


class GameObject(object, metaclass=GameObjectMeta):
    pass


class TimeLimitExceeded(Timeout, GameObject):
    pass


class GameException(Exception, GameObject):
    def __init__(self, msg=None, **kwargs):
        Exception.__init__(self, msg)
        self.__dict__.update(kwargs)


class GameError(GameException):
    pass


class InterruptActionFlow(GameException):
    def __init__(self, unwind_to=None):
        GameException.__init__(self)
        self.unwind_to = unwind_to


class AssociatedDataViralContext(ViralContext):
    VIRAL_SEARCH: List[str] = []
    _: dict

    def viral_import(self, _):
        self._ = defaultdict(bool)


class Player(GameObject, AssociatedDataViralContext):
    uid: int

    def reveal(self, obj_list: Any) -> None:
        raise GameError('Abstract')

    def __repr__(self):
        return self.__class__.__name__


class NPC(object):
    __slots__ = ('name', 'input_handler')

    def __init__(self, name, input_handler):
        self.name = name
        self.input_handler = input_handler


class GameEnded(GameException):
    winners: Sequence[Player]

    def __init__(self, winners: Sequence[Player]):
        GameException.__init__(self)
        self.winners = winners


class GameViralContext(ViralContext):
    VIRAL_SEARCH = ['g', 'self']
    game: 'Game'

    def viral_import(self, g):
        self.game = g

    def viral_export(self):
        return self.game


class Game(GameObject, GameViralContext):
    IS_DEBUG = False

    # ----- Class Variables -----
    CLIENT: ClassVar[bool]
    SERVER: ClassVar[bool]
    n_persons: ClassVar[int]
    npc_players: ClassVar[List[NPC]] = []
    params_def: ClassVar[Dict[str, Any]] = {}
    bootstrap: ClassVar[Type[BootstrapAction]]
    dispatcher_cls: ClassVar[Type[EventDispatcher]]

    # ----- Instance Variables -----
    game: Game
    dispatcher: EventDispatcher
    event_observer: Optional[EventHandler]
    action_stack: List[Action]
    hybrid_stack: List[Union[Action, EventHandler]]
    ended: bool
    winners: Sequence[Player]
    random: Random
    _: dict

    def __init__(self) -> None:
        self.game = self

        self.action_stack   = []
        self.hybrid_stack   = []
        self.ended          = False
        self.winners        = []
        self.turn_count     = 0
        self.event_observer = None

        self._ = {}

        self.refresh_dispatcher()

    def refresh_dispatcher(self) -> None:
        self.dispatcher = self.dispatcher_cls(self)

    def emit_event(self, evt_type: str, data: Any) -> Any:
        ob = self.event_observer
        if ob:
            data = ob.handle(evt_type, data)

        return self.dispatcher.emit(evt_type, data)

    def process_action(self, action: Action) -> bool:
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
            log.debug('applying action %s' % action.__class__.__name__)
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

    def pause(self, t: float) -> None:
        pass

    def get_synctag(self) -> int:
        raise GameError('Abstract')

    def is_dropped(self, p: Player) -> bool:
        raise GameError('Abstract')

    def name_of(self, p: Player) -> str:
        raise GameError('Abstract')

    def can_leave(self, p: Player) -> bool:
        raise GameError('Abstract')


class ActionShootdown(BaseException, GameObject):
    def __bool__(self):
        return False


class EventHandler(GameObject):
    interested: List[str]
    execute_before: List[str] = []
    execute_after: List[str]  = []

    arbiter: Optional[Type[EventArbiter]] = None

    def __init__(self, g: Game):
        self.game = g

    def handle(self, evt_type: str, data: Any):
        raise GameError('Override handle function to implement EventHandler logics!')

    def get_interested(self):
        interested = self.interested
        assert isinstance(interested, (list, tuple)), "Should specify interested events! %r" % self.__class__
        return list(interested)

    @staticmethod
    def make_list(g, eh_classes, fold_arbiter=True):
        table = {}
        eh_classes = set(eh_classes)
        arbiters: Any = defaultdict(list)

        for cls in eh_classes:
            assert not issubclass(cls, EventArbiter), 'Should not pass arbiters in make_list, %r' % cls
            grp = cls.arbiter if fold_arbiter else None
            if grp is not None:
                arbiters[grp].append(cls)
                cls = grp

            table[cls.__name__] = cls(g)

        for a, lst in arbiters.items():
            eh = table[a.__name__]
            eh.set_handlers(EventHandler.make_list(g, lst, fold_arbiter=False))

        allnames = frozenset(table)

        for eh in table.values():
            eh.execute_before = set(eh.execute_before) & allnames  # make it instance var
            eh.execute_after = set(eh.execute_after) & allnames

        for clsname, eh in table.items():
            for before in eh.execute_before:
                table[before].execute_after.add(clsname)

            for after in eh.execute_after:
                table[after].execute_before.add(clsname)

        lst = list(table.values())
        lst.sort(key=lambda v: v.__class__.__name__)  # must sync between server and client

        toposorted = []
        while lst:
            deferred = []
            commit = []
            for eh in lst:
                if not eh.execute_after:
                    for b in eh.execute_before:
                        table[b].execute_after.remove(eh.__class__.__name__)
                    commit.append(eh)
                else:
                    deferred.append(eh)

            if not commit:
                raise GameError("Can't resolve dependencies! Check for circular reference!")

            toposorted.extend(commit)
            lst = deferred

        return toposorted

    @staticmethod
    def _dump_eh_dependency_graph():
        ehs: Set[Type[EventHandler]] = {i for i in all_gameobjects if issubclass(i, EventHandler)}
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


class EventArbiter(EventHandler):
    handlers = ()

    def set_handlers(self, handlers):
        self.handlers = handlers[:]


T = TypeVar('T', bound=EventHandler)


class EventDispatcher(GameObject):
    game: Game
    _event_handlers: Sequence[EventHandler]
    _adhoc_ehs: List[EventHandler]
    _ehs_cache: Dict[str, List[EventHandler]]

    def __init__(self, g: Game):
        self.game = g

        self._adhoc_ehs     = []
        self._ehs_cache     = {}
        self._event_handlers = self.populate_handlers()

    def add_adhoc(self, eh: EventHandler):
        self._adhoc_ehs.insert(0, eh)

    def remove_adhoc(self, eh: EventHandler):
        try:
            self._adhoc_ehs.remove(eh)
        except ValueError:
            pass

    def populate_handlers(self) -> Sequence[EventHandler]:
        raise Exception('Override this!')

    def emit(self, evt_type: str, data: Any):
        '''
        Fire an event, all relevant event handlers will see this,
        data can be modified.
        '''
        random.random() < 0.01 and gevent.sleep(0.00001)  # prevent buggy logic code blocking scheduling
        if isinstance(data, (list, tuple, str)):
            s = data
        else:
            s = data.__class__.__name__
        log.debug('emit_event: %s %s' % (evt_type, s))

        if evt_type in ('action_before', 'action_apply', 'action_after'):
            action_event = True
            assert isinstance(data, Action)
        else:
            action_event = False

        adhoc = self._adhoc_ehs
        ehs = self._get_relevant_eh(evt_type)

        for l in adhoc, ehs:
            for eh in l:
                data = self.handle_single_event(eh, evt_type, data)
                if action_event and data.cancelled:
                    break

        return data

    def handle_single_event(self, eh: EventHandler, *a, **k):
        try:
            self.game.hybrid_stack.append(eh)
            data = eh.handle(*a, **k)
        finally:
            rst = eh is self.game.hybrid_stack.pop()
            assert rst

        if data is None:
            raise Exception('EventHandler %s returned None' % eh.__class__.__name__)

        return data

    def find_by_cls(self, cls: Type[T]) -> Optional[T]:
        for c in self._event_handlers:
            if isinstance(c, cls):
                return c

        return None

    def _get_relevant_eh(self, tag: str):
        ehs = self._ehs_cache.get(tag)
        if ehs is not None:
            return ehs

        ehs = [
            eh for eh in self._event_handlers if
            tag in eh.get_interested()
        ]
        self._ehs_cache[tag] = ehs

        return ehs


class Action(GameObject, GameViralContext, AssociatedDataViralContext):
    cancelled = False
    done = False
    invalid = False
    succeeded: bool

    def action_shootdown_exception(self) -> None:
        if not self.is_valid():
            raise ActionShootdown(self)

        _ = self.game.emit_event('action_shootdown', self)
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


class SyncPrimitive(GameObject):
    def __init__(self, value):
        self.value = value

    def sync(self, data):
        self.value = self.value.__class__(data)

    def __data__(self):
        return self.value

    def __repr__(self):
        return self.value.__repr__()


T_sync = TypeVar('T_sync', bound=Union[list, int, str, bool])


def sync_primitive(val: T_sync, to: Union[Player, BatchList[Player]]) -> T_sync:
    if not to:  # sync to nobody
        return val

    rst: Any = None
    if isinstance(val, list):
        lst = [SyncPrimitive(i) for i in val]
        to.reveal(lst)
        rst = val.__class__(
            i.value for i in lst
        )
    else:
        v = SyncPrimitive(val)
        to.reveal(v)
        rst = v.value

    return rst


def get_seed_for(g: Game, p: Union[Player, BatchList[Player]]):
    from game.autoenv import Game
    if Game.SERVER:
        seed = g.random.getrandbits(63)
    else:
        seed = 0

    return sync_primitive(seed, p)


def list_shuffle(g, lst, plain_to):
    seed = get_seed_for(g, plain_to)

    if seed:  # cardlist owner & server
        shuffler = random.Random(seed)
        shuffler.shuffle(lst)
    else:  # others
        for i in lst:
            i.conceal()


class Inputlet(GameObject, GameViralContext):
    '''
    NOTICE: Inputlet instance variable should
            not be used as a side channel to pass infomation
            in game logic code.
    '''
    initiator: Any
    timeout: int
    actor: object

    @classmethod
    def tag(cls):
        clsname = cls.__name__
        assert clsname.endswith('Inputlet')
        return clsname[:-8]

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
        return f'<I:{self.tag()}>'


class InputTransaction(GameViralContext):
    def __init__(self, name: str, involved: Sequence[Any], **kwargs):
        self.name = name
        self.involved = involved[:]
        self.__dict__.update(kwargs)

    def __enter__(self):
        return self.begin()

    def begin(self):
        g = self.game
        g.emit_event('user_input_transaction_begin', self)
        return self

    def __exit__(self, *excinfo):
        self.end()
        return False

    def end(self):
        g = self.game
        g.emit_event('user_input_transaction_end', self)

    def notify(self, evt_name, arg):
        '''
        Event For UI
        '''
        self.game.emit_event('user_input_transaction_feedback', (self, evt_name, arg))

    def __repr__(self):
        return '<T:{}>'.format(self.name)


class Packet(object):
    __slots__ = ('tag', 'data', 'consumed')

    def __init__(self, tag: str, data: object):
        self.tag = tag
        self.data = data
        self.consumed = False

    def __repr__(self):
        return 'Packet<%s, %s, %s>' % (self.tag, self.data, '_X'[self.consumed])


class GameArchive(TypedDict):
    send: List[Tuple[str, Any]]  # tag, data
    recv: List[Tuple[str, Any]]  # tag, data


class GameData(object):
    def __init__(self, gid: int, live=True):
        self.gid = gid
        self._send: List[Packet] = []
        self._recv: List[Packet] = []
        self._seen: Set[str] = set()
        self._pending_recv: List[Packet] = []
        self._has_data = Event()
        self._dead = False
        self._live = live

        self._in_gexpect = False

    def feed_recv(self, tag: str, data: object):
        if tag in self._seen:
            return

        self._seen.add(tag)
        p = Packet(tag, data)
        self._recv.append(p)
        self._pending_recv.append(p)
        self._has_data.set()

    def feed_send(self, tag: str, data: object):
        p = Packet(tag, data)
        self._send.append(p)
        return p

    def get_sent(self) -> List[Packet]:
        return self._send

    def is_live(self) -> bool:
        return self._live

    def gexpect(self, tag: str):
        if self._dead:
            raise EndpointDied

        try:
            assert not self._in_gexpect, 'NOT REENTRANT'
            self._in_gexpect = True

            log.debug('GAME_EXPECT: %s', repr(tag))

            recv = self._pending_recv
            e = self._has_data
            e.clear()

            glob = False
            if tag.endswith('*'):
                tag = tag[:-1]
                glob = True

            while True:
                livepkt = None
                for i, packet in enumerate(recv):
                    if isinstance(packet, EndpointDied):
                        del recv[i]
                        raise packet

                    if packet.tag == '__game_live':
                        livepkt = packet
                        continue

                    if packet.tag == tag or (glob and packet.tag.startswith(tag)):
                        log.debug('GAME_READ: %s', repr(packet))
                        del recv[i]
                        packet.consumed = True
                        if livepkt:
                            self._live = True
                        return [packet.tag, packet.data]

                    else:
                        log.debug('GAME_MISS: %s, EXPECTS: %s, GID: %s', repr(packet), tag, self.gid)

                e.wait(timeout=5)
                if self._dead:
                    raise EndpointDied
                e.clear()
        finally:
            self._in_gexpect = False

    def die(self) -> None:
        # Explanation:
        # When sb. exit game in input state,
        # the others must wait until his timeout exceeded.
        # called this to break such condition.
        self._dead = True
        self._has_data.set()

    def revive(self) -> None:
        self._dead = False

    def archive(self) -> GameArchive:
        return {
            'send': [(i.tag, i.data) for i in self._send],
            'recv': [(i.tag, i.data) for i in self._recv],
        }

    def feed_archive(self, data: GameArchive) -> None:
        recv = [Packet(t, d) for t, d in data['recv']]
        self._recv = recv
        self._pending_recv = list(recv)
        self._has_data.set()


class GameItem(object):
    inventory: Dict[str, Type[GameItem]] = {}

    # --- class ---
    key: str  = ''
    args: List[type] = []
    usable = False

    title = 'ITEM-TITLE'
    description = 'ITEM-DESC'

    # --- instance ---
    sku: str

    # --- poison ---
    init: None

    def __init__(self, *args):
        raise Exception('Should not instantiate plain GameItem!')

    def should_usable(self, g: ServerGame, u: Client) -> None:
        ...

    @classmethod
    def register(cls, item_cls):
        assert issubclass(item_cls, cls)
        cls.inventory[item_cls.key] = item_cls
        return item_cls

    @classmethod
    def from_sku(cls, sku) -> 'GameItem':
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

        o = cls(*args)
        o.sku = sku
        return o


class BootstrapAction(Action):
    def __init__(self, params: Dict[str, Any],
                       items: Dict[Player, List[GameItem]],
                       players: BatchList[Player]):
        raise Exception('Override this!')
