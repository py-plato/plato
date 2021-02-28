import random
from collections import defaultdict
from hashlib import blake2b
from typing import Any, Dict, Type


class Context:
    def __init__(
        self, hasher: blake2b, parent: "Context" = None, meta: Dict[Any, Any] = None
    ):
        self._hasher = hasher
        self.parent = parent
        if meta is None:
            meta = {}
        self.meta = meta

        self.seed = self._hasher.digest()
        self.rng = random.Random(self.seed)

    def subcontext(self, class_name: str) -> "Context":
        subhasher = self._hasher.copy()
        subhasher.update(class_name.encode())
        return Context(subhasher, self, dict(self.meta))


def seed(value: int):
    global _type_counts
    _type_counts = defaultdict(lambda: value)


def _int2bytes(value: int) -> bytes:
    return value.to_bytes(value.bit_length() // 8 + 1, "big")


def _create_hasher(seed: int) -> blake2b:
    hasher = blake2b()
    hasher.update(_int2bytes(seed))
    return hasher


_type_counts = defaultdict(lambda: 0)


def get_root_context(type_: Type):
    seed = _type_counts[type_]
    _type_counts[type_] += 1
    return Context(_create_hasher(seed))