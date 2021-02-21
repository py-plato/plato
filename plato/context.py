import random
from collections import defaultdict
from hashlib import blake2b
from typing import Dict


class Context:
    def __init__(self, hasher: blake2b):
        self._hasher = hasher
        self._type_counts: Dict[str, int] = defaultdict(lambda: 0)

        self.seed = self._hasher.digest()
        self.rng = random.Random(self.seed)

    def subcontext(self, class_name: str) -> "Context":
        subhasher = self._hasher.copy()
        subhasher.update(class_name.encode())
        subhasher.update(_int2bytes(self._type_counts[class_name]))
        self._type_counts[class_name] += 1

        return Context(subhasher)


def seed(value: int):
    global _root
    _root = Context(_create_hasher(value))
    return _root


def _int2bytes(value: int) -> bytes:
    return value.to_bytes(value.bit_length() // 8 + 1, "big")


def _create_hasher(seed: int) -> blake2b:
    hasher = blake2b()
    hasher.update(_int2bytes(seed))
    return hasher


def get_root():
    return _root


_root = Context(_create_hasher(0))