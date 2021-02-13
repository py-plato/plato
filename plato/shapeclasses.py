from dataclasses import dataclass
import hashlib
from typing import Type

from .context import Context
from .providers import Provider


def shapeclass(cls):
    dc = dataclass(cls)
    _patch_init(dc)
    return dc


_seed = 0
_seeds = {}


def seed(seed: int):
    global _seed, _seeds
    _seed = seed
    _seeds.clear()


def _patch_init(instance):
    original_init = instance.__init__

    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)

        seed = _seeds.get(self.__class__, _seed)
        _seeds[self.__class__] = seed + 1

        for field_name in dir(instance):
            field = getattr(self, field_name)
            if isinstance(field, Provider):
                field_seed = _derive_field_seed(seed, instance.__class__, field_name)
                setattr(self, field_name, field.sample(Context(field_seed)))

    instance.__init__ = __init__


def _derive_field_seed(base_seed: int, cls: Type, field_name: str) -> bytes:
    hasher = hashlib.blake2b()
    cls = hash(cls)
    hasher.update(cls.to_bytes(cls.bit_length() // 8 + 1, "big"))
    hasher.update(field_name.encode())
    hasher.update(base_seed.to_bytes(base_seed.bit_length() // 8 + 1, "big"))
    return hasher.digest()