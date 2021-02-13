from dataclasses import dataclass

from .context import Context
from .providers import Provider


def shapeclass(cls):
    dc = dataclass(cls)
    _patch_init(dc)
    return dc


def _patch_init(instance):
    original_init = instance.__init__

    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        for field_name in dir(instance):
            field = getattr(self, field_name)
            if isinstance(field, Provider):
                setattr(self, field_name, field.sample(Context()))

    instance.__init__ = __init__