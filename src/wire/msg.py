# -*- coding: utf-8 -*-
from __future__ import annotations

# -- stdlib --
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar
from typing_extensions import TypedDict

# -- third party --
from dataclasses import dataclass
import dataclasses

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
        env = {}
        fields = [f"    '{i.name}': self.{i.name}," for i in dataclasses.fields(cls)]
        code = (
            "def encode(self) -> dict:"
            "    return {"
            "        'op': self.op,"
            "        %s"
            "    }"
        ) % '\n'.join(fields)
        exec(code, env)
        cls.encode = env['encode']

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


@message
@dataclass
class PlayerPresence(Message, ServerToClient):
    '''
    Indicates if player is still in the game
    '''
    gid: int
    presence: Dict[int, bool]


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
    uid: int
    name: str
    gid: int
    type: str


@message
@dataclass
class ObserveRequest(Message, ServerToClient):
    uid: int


@message
@dataclass
class KickRequest(Message, ServerToClient):
    uid: int
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
    uid: int


@message
@dataclass
class Ping(Message, ServerToClient):
    pass


# --------------------------------
# ----- system -----
@message
@dataclass
class Beat(Message, ClientToServer):
    pass


@message
@dataclass
class Pong(Message, ClientToServer):
    pass


@message
@dataclass
class Auth(Message, ClientToServer):
    token: str


# ----- room -----
class CreateRoomFlags(TypedDict):
    match: bool
    invite: bool


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


# ----- observe -----
@message
@dataclass
class Observe(Message, ClientToServer):
    uid: int


@message
@dataclass
class GrantObserve(Message, ClientToServer):
    uid: int
    grant: bool


@message
@dataclass
class KickObserver(Message, ClientToServer):
    uid: int


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
    uid: int


@message
@dataclass
class Kick(Message, ClientToServer):
    uid: int


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
    uid: int


@message
@dataclass
class AdminKillGame(Message, ClientToServer):
    gid: int


@message
@dataclass
class AdminAdd(Message, ClientToServer):
    uid: int


@message
@dataclass
class AdminRemove(Message, ClientToServer):
    uid: int


@message
@dataclass
class AdminAddBigbrother(Message, ClientToServer):
    uid: int


@message
@dataclass
class AdminRemoveBigbrother(Message, ClientToServer):
    uid: int


# ----- match -----
@message
@dataclass
class SetupMatch(Message, ClientToServer):
    name: str
    mode: str
    uids: List[int]
