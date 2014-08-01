# -*- coding: utf-8 -*-


class ParamDefinition(object):
    options = (False, True)

    # dict key
    class __metaclass__(type):
        def __str__(self):
            return self.__name__

        def __eq__(self, other):
            return self.__name__ == other

        def __hash__(self):
            return hash(self.__name__)

    def __init__(self, default_value):
        self.default_value = default_value


class RandomSeat(ParamDefinition):
    pass


class NoImbaCharacters(ParamDefinition):
    pass
