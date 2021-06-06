"""Provides a dictionary indexed by object identity with a weak reference."""

import weakref
from typing import Any, Dict, Generic, Iterator, TypeVar

T = TypeVar("T")


class WeakIdDict(Generic[T]):
    """Dictionary using object identity with a weak reference as key."""

    data: Dict[int, T]
    refs: Dict[int, weakref.ref]

    def __init__(self) -> None:
        self.data = {}
        self.refs = {}

    def __getitem__(self, obj_key: Any) -> T:
        return self.data[id(obj_key)]

    def __setitem__(self, obj_key: Any, value: T) -> None:
        id_key = id(obj_key)

        def clean_stale_ref(_: weakref.ref) -> None:
            del self.data[id_key]
            del self.refs[id_key]

        self.refs[id_key] = weakref.ref(obj_key, clean_stale_ref)
        self.data[id_key] = value

    def __delitem__(self, obj_key: Any) -> None:
        id_key = id(obj_key)
        del self.data[id_key]
        del self.refs[id_key]

    def __iter__(self) -> Iterator[Any]:
        for ref in self.refs.values():
            strong_ref = ref()
            if strong_ref:
                yield strong_ref

    def __len__(self) -> int:
        return len(self.data)
