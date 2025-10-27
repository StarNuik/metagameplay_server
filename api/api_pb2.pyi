from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class LoginReq(_message.Message):
    __slots__ = ("username",)
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    username: str
    def __init__(self, username: _Optional[str] = ...) -> None: ...

class UserSession(_message.Message):
    __slots__ = ("session_token",)
    SESSION_TOKEN_FIELD_NUMBER: _ClassVar[int]
    session_token: str
    def __init__(self, session_token: _Optional[str] = ...) -> None: ...

class BuyItemReq(_message.Message):
    __slots__ = ("item_name",)
    ITEM_NAME_FIELD_NUMBER: _ClassVar[int]
    item_name: str
    def __init__(self, item_name: _Optional[str] = ...) -> None: ...

class SellItemReq(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ItemsList(_message.Message):
    __slots__ = ("items",)
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    items: _containers.RepeatedCompositeFieldContainer[Item]
    def __init__(self, items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ("username", "credits", "items")
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    CREDITS_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    username: str
    credits: int
    items: _containers.RepeatedCompositeFieldContainer[Item]
    def __init__(self, username: _Optional[str] = ..., credits: _Optional[int] = ..., items: _Optional[_Iterable[_Union[Item, _Mapping]]] = ...) -> None: ...

class Item(_message.Message):
    __slots__ = ("name", "price")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PRICE_FIELD_NUMBER: _ClassVar[int]
    name: str
    price: int
    def __init__(self, name: _Optional[str] = ..., price: _Optional[int] = ...) -> None: ...
