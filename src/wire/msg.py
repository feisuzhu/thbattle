# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, TypedDict
import dataclasses

# -- third party --
# -- own --
from . import model


# -- code --
class ServerToClient:
    pass


class ClientToServer:
    pass


class BiDirectional(ServerToClient, ClientToServer):
    pass


class Message:
    types: ClassVar[Dict[str, Type[Message]]] = {}
    op: str

    def __init__(self, *args, **kwargs):
        raise Exception('Abstract')

    def encode(self) -> dict:
        ...

    @classmethod
    def decode(cls, data: dict) -> Optional[Message]:
        data = dict(data)
        op = data.pop('op', '')
        if op not in cls.types:
            return None

        return cls.types[op](**data)


def message(cls: Type[Message]) -> Type[Message]:
    assert issubclass(cls, ServerToClient) or issubclass(cls, ClientToServer)
    cls.op = cls.__name__
    assert cls.op not in Message.types, cls.op
    Message.types[cls.op] = cls

    if cls.encode is Message.encode:
        env: Any = {}
        fields = [f"    '{i.name}': self.{i.name}," for i in dataclasses.fields(cls)]
        code = (
            "def encode(self) -> dict:"
            "    return {"
            "        'op': self.op,"
            "        %s"
            "    }"
        ) % '\n'.join(fields)
        exec(code, env)
        cls.encode = env['encode']  # type: ignore

    return cls


T = TypeVar('T', bound=Message)


def cast(typ: Type[T], msg: Message) -> Optional[T]:
    if msg.op == typ.op:
        return msg  # type: ignore

    return None


# ----------------------------
@message
@dataclass
class Info(Message, ServerToClient):
    msg: str


@message
@dataclass
class Error(Message, ServerToClient):
    msg: str


@message
@dataclass
class SystemMsg(Message, ServerToClient):
    msg: str


@message
@dataclass
class CurrentGames(Message, ServerToClient):
    games: List[model.Game]


@message
@dataclass
class CurrentUsers(Message, ServerToClient):
    users: List[model.User]


@message
@dataclass
class LobbyStatus(Message, ServerToClient):
    total_users: int
    gaming_users: int


@message
@dataclass
class RoomUsers(Message, ServerToClient):
    gid: int
    users: List[model.User]


@message
@dataclass
class GameJoined(Message, ServerToClient):
    game: model.GameDetail


@message
@dataclass
class GameStarted(Message, ServerToClient):
    game: model.GameDetail


class PresenceState(IntEnum):
    ONLINE  = 1
    DROPPED = 2
    FLED    = 3


@message
@dataclass
class PlayerPresence(Message, ServerToClient):
    '''
    Indicates if player is still in the game
    '''
    gid: int
    presence: List[PresenceState]


@message
@dataclass
class GameEnded(Message, ServerToClient):
    gid: int


@message
@dataclass
class GameParams(Message, ServerToClient):
    gid: int
    params: Dict[str, Any]


@message
@dataclass
class SetGameParam(Message, BiDirectional):
    gid: int
    pid: int
    key: str
    value: Any


@message
@dataclass
class GameData(Message, BiDirectional):
    gid: int
    tag: str
    data: Any


@message
@dataclass
class InviteRequest(Message, ServerToClient):
    pid: int
    gid: int
    type: str


@message
@dataclass
class ObserveRequest(Message, ServerToClient):
    pid: int


@message
@dataclass
class KickRequest(Message, ServerToClient):
    pid: int
    victim: int
    votes: int


@message
@dataclass
class ObserveStarted(Message, ServerToClient):
    game: model.GameDetail
    observee: int


@message
@dataclass
class GameLeft(Message, ServerToClient):
    gid: int


@message
@dataclass
class Greeting(Message, ServerToClient):
    node: str
    version: str


@message
@dataclass
class AuthError(Message, ServerToClient):
    reason: str


@message
@dataclass
class AuthSuccess(Message, ServerToClient):
    pid: int


# --------------------------------
# ----- system -----
@message
@dataclass
class Beat(Message, ClientToServer):
    pass


@message
@dataclass
class Auth(Message, ClientToServer):
    token: str


# ----- room -----
class CreateRoomFlags(TypedDict, total=False):
    invite: bool
    chat: bool


@message
@dataclass
class CreateRoom(Message, ClientToServer):
    name: str
    mode: str
    flags: CreateRoomFlags


@message
@dataclass
class JoinRoom(Message, ClientToServer):
    gid: int
    slot: Optional[int]


@message
@dataclass
class LeaveRoom(Message, ClientToServer):
    pass


@message
@dataclass
class GetRoomUsers(Message, ClientToServer):
    gid: int


@message
@dataclass
class GetReady(Message, ClientToServer):
    pass


@message
@dataclass
class CancelReady(Message, ClientToServer):
    pass


@message
@dataclass
class ChangeLocation(Message, ClientToServer):
    loc: int


# ----- matching -----
@message
@dataclass
class StartMatching(Message, BiDirectional):
    modes: List[str]


@message
@dataclass
class QueryMatching(Message, ClientToServer):
    pass


@message
@dataclass
class CurrentMatching(Message, ServerToClient):
    matches: Dict[str, List[int]]  # mode -> [pid, ...]


# ----- observe -----
@message
@dataclass
class Observe(Message, ClientToServer):
    pid: int


@message
@dataclass
class GrantObserve(Message, ClientToServer):
    pid: int
    grant: bool


@message
@dataclass
class KickObserver(Message, ClientToServer):
    pid: int


@message
@dataclass
class ObserverEnter(Message, ServerToClient):
    observer: int
    observee: int


@message
@dataclass
class ObserverLeave(Message, ServerToClient):
    observer: int
    observee: int


# ----- invite -----
@message
@dataclass
class Invite(Message, ClientToServer):
    pid: int


@message
@dataclass
class Kick(Message, ClientToServer):
    pid: int


# ----- item -----
@message
@dataclass
class UseItem(Message, ClientToServer):
    sku: str


# ----- admin -----
@message
@dataclass
class AdminStacktrace(Message, ClientToServer):
    pass


@message
@dataclass
class AdminClearZombies(Message, ClientToServer):
    pass


@message
@dataclass
class AdminMigrate(Message, ClientToServer):
    pass


@message
@dataclass
class AdminKick(Message, ClientToServer):
    pid: int


@message
@dataclass
class AdminKillGame(Message, ClientToServer):
    gid: int


@message
@dataclass
class AdminAdd(Message, ClientToServer):
    pid: int


@message
@dataclass
class AdminRemove(Message, ClientToServer):
    pid: int


@message
@dataclass
class AdminAddBigbrother(Message, ClientToServer):
    pid: int


@message
@dataclass
class AdminRemoveBigbrother(Message, ClientToServer):
    pid: int


# ----- contest -----
@message
@dataclass
class SetupContest(Message, ClientToServer):
    name: str
    mode: str
    pids: List[int]
