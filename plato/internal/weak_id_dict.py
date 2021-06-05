"""Provides a dictionary indexed by object identity with a weak reference."""

import weakref
from typing import Generic, TypeVar

T = TypeVar("T")


class WeakIdDict(Generic[T]):
    """Dictionary using object identity with a weak reference as key."""

    def __init__(self):
        self.data = {}
        self.refs = {}

    def __getitem__(self, obj_key: object) -> T:
        return self.data[id(obj_key)]

    def __setitem__(self, obj_key: object, value: T):
        id_key = id(obj_key)

        def clean_stale_ref(_):
            del self.data[id_key]
            del self.refs[id_key]

        self.refs[id_key] = weakref.ref(obj_key, clean_stale_ref)
        self.data[id_key] = value

    def __delitem__(self, obj_key: object):
        id_key = id(obj_key)
        del self.data[id_key]
        del self.refs[id_key]

    def __iter__(self):
        for ref in self.refs.values():
            strong_ref = ref()
            if strong_ref:
                yield strong_ref

    def __len__(self):
        return len(self.data)
