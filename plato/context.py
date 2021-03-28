"""Context management"""

import random
from collections import defaultdict
from hashlib import blake2b
from typing import Any, Dict, Type

from typing_extensions import Protocol


class Hasher(Protocol):
    """Protocol of classes to perform incremental hashing."""

    def copy(self) -> "Hasher":
        """Create a copy of the current hasher state."""
        ...

    def update(self, data: bytes):
        """Update the hash with *data*."""
        ...

    def digest(self) -> bytes:
        """Return the current hash."""
        ...


class Context:
    """Context used in sampling from `.Provider` instances.

    Arguments
    ---------
    hasher: Hasher
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
        self, hasher: Hasher, parent: "Context" = None, meta: Dict[Any, Any] = None
    ):
        self._hasher = hasher
        self.parent = parent
        if meta is None:
            meta = {}
        self.meta = meta

        self.seed = self._hasher.digest()
        self.rng = random.Random(self.seed)

    def subcontext(self, name: str) -> "Context":
        """Derive a subcontext.

        A subcontext is derived by updating a copy of the *hasher* with the
        *name*, setting the *parent* accordingly, and (flat) copying the
        *meta* dictionary.

        Arguments
        ---------
        name: str
            A name to identify the subcontext. Reusing the same name will give
            a subcontext with the same random number seed.

        Returns
        -------
        Context
            The derived subcontext.
        """
        subhasher = self._hasher.copy()
        subhasher.update(name.encode())
        return Context(subhasher, self, dict(self.meta))


_TYPE_COUNTS: Dict[Type, int] = defaultdict(lambda: 0)


def seed(value: int):
    """Set the global Plato base seed."""
    # pylint: disable=global-statement
    global _TYPE_COUNTS
    _TYPE_COUNTS = defaultdict(lambda: value)


def _int2bytes(value: int) -> bytes:
    return value.to_bytes(value.bit_length() // 8 + 1, "big")


def _create_hasher(hasher_seed: int) -> blake2b:
    hasher = blake2b()
    hasher.update(_int2bytes(hasher_seed))
    return hasher


def get_root_context(type_: Type) -> Context:
    """Get a root context for a given type."""
    root_seed = _TYPE_COUNTS[type_]
    _TYPE_COUNTS[type_] += 1
    return Context(_create_hasher(root_seed))
