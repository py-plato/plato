"""Context management"""

import random
from collections import defaultdict
from hashlib import blake2b
from typing import Any, Dict, Type


class Context:
    """Context used in sampling from `.Provider` instances.

    Arguments
    ---------
    hasher: hashlib.blake2b
        Hasher used to derive the random number seed and to derive hashers for
        subcontexts.
    parent: Context, optional
        The parent context if any.
    meta: dict, optional
        A dictionary that can be used by `.Provider` instances to store
        additional information in the context. Be aware that the passed instance
        might be modified.

    Attributes
    ----------

    parent: Context
        The parent context or `None` if this is a root context.
    meta: dict
        Dictionary that can be used by providers to store additional information
        across invocations of `.Provider.sample()`. Use the `.Provider` instance
        or concrete class as key to avoid key collisions with other providers.
    seed: bytes
        Seed to use for the generation of random numbers.
    rng: random.Random
        A seeded random number generator that may be used for the generation of
        random numbers.
    """

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
    """Set the global Plato base seed."""
    global _type_counts
    _type_counts = defaultdict(lambda: value)


def _int2bytes(value: int) -> bytes:
    return value.to_bytes(value.bit_length() // 8 + 1, "big")


def _create_hasher(seed: int) -> blake2b:
    hasher = blake2b()
    hasher.update(_int2bytes(seed))
    return hasher


_type_counts = defaultdict(lambda: 0)


def get_root_context(type_: Type) -> Context:
    """Get a root context for a given type."""
    seed = _type_counts[type_]
    _type_counts[type_] += 1
    return Context(_create_hasher(seed))
