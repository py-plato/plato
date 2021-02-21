from copy import deepcopy
from dataclasses import dataclass, is_dataclass, replace
from typing import Any, ClassVar

from .context import get_root
from .providers import Provider


class _ShapeclassProvider(type):
    def sample(self, context):
        return self()


Provider.register(_ShapeclassProvider)


def shapeclass(cls):
    return dataclass(cls)


def sample(shape, context=None):
    if context is None:
        context = get_root()

    if isinstance(shape, Provider):
        return shape.sample(context)

    x = deepcopy(shape)
    context = context.subcontext(x.__class__.__name__)

    for field_name in x.__annotations__:
        type_ = x.__annotations__.get(field_name, ClassVar[Any])
        if (
            hasattr(type_, "__origin__")
            and getattr(type_, "__origin__") is ClassVar[Any].__origin__
        ):
            continue
        field = getattr(x, field_name)
        if is_dataclass(field):
            value = sample(
                field, context.subcontext(field_name)
            )  # FIXME field vs class name?
            setattr(x, field_name, value)
        elif isinstance(field, Provider):
            value = field.sample(context.subcontext(field_name))
            setattr(x, field_name, value)
    for field_name in dir(x):
        if field_name in x.__annotations__ or field_name in x.__class__.__dict__:
            continue
        if field_name == "__class__":
            continue
        field = getattr(x, field_name)
        if is_dataclass(field):
            value = sample(
                field, context.subcontext(field_name)
            )  # FIXME field vs class name?
            setattr(x, field_name, value)
        elif isinstance(field, Provider):
            value = field.sample(context.subcontext(field_name))
            setattr(x, field_name, value)
    return x