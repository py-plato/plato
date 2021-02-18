from dataclasses import dataclass
from typing import Any, ClassVar

from .context import ProtoContext
from .providers import Provider


class _ShapeclassProvider(type):
    def sample(self, context):
        return self()


Provider.register(_ShapeclassProvider)


def shapeclass(cls):
    @dataclass
    class ShapeImpl(dataclass(cls), metaclass=_ShapeclassProvider):
        def __post_init__(self, *args, **kwargs):
            # FIXME calls super post init if existant
            with ProtoContext.current().subcontext(self.__class__.__name__) as ctx:
                for field_name in dir(self):
                    if field_name == "__class__":
                        continue
                    type_ = self.__annotations__.get(field_name, ClassVar[Any])
                    if (
                        hasattr(type_, "__origin__")
                        and getattr(type_, "__origin__") is ClassVar[Any].__origin__
                    ):
                        continue
                    field = getattr(self, field_name)
                    if isinstance(field, Provider):
                        value = field.sample(ctx.field_context(field_name))
                        setattr(self, field_name, value)

    ShapeImpl.__name__ = cls.__name__
    ShapeImpl.__doc__ = cls.__doc__

    return ShapeImpl
