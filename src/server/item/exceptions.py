from utils import BusinessException


class UserNotFound(BusinessException):
    pass


class BackpackFull(BusinessException):
    pass


class InsufficientFunds(BusinessException):
    pass


class ItemNotFound(BusinessException):
    pass


class InvalidCurrency(BusinessException):
    pass


class TooManySellingItems(BusinessException):
    pass


class InvalidItemSKU(BusinessException):
    pass


class ItemNotUsable(BusinessException):
    pass
