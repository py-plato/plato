from dataclasses import dataclass
import hashlib
from typing import Type

from .context import ProtoContext
from .providers import Provider


def shapeclass(cls):
    dc = dataclass(cls)
    _patch_init(dc)
    return dc


def _patch_init(instance):
    original_init = instance.__init__

    def __init__(self, *args, **kwargs):
        with ProtoContext.current().subcontext(self.__class__.__name__) as ctx:
            original_init(self, *args, **kwargs)

            for field_name in dir(instance):
                field = getattr(self, field_name)
                if isinstance(field, Provider):
                    value = field.sample(ctx.field_context(field_name))
                    setattr(self, field_name, value)

    instance.__init__ = __init__