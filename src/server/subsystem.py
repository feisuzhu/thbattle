from utils import instantiate


@instantiate
class Subsystem(object):
    __slots__ = (
        'lobby',
        'item',
        'interconnect',
    )
