from copy import deepcopy
from dataclasses import is_dataclass, make_dataclass, Field, fields
from typing import Any, ClassVar
from weakref import WeakKeyDictionary

from .context import get_root
from .providers import Provider


_post_init_registry = WeakKeyDictionary()


def formclass(cls):
    post_init_fns = {}

    annotations = getattr(cls, "__annotations__", {})
    fields = [
        (name, type_)
        for name, type_ in annotations.items()
        if not _is_classvar_type(type_)
    ]

    namespace = {}
    for name, value in cls.__dict__.items():
        if name in {"__annotations__", "__dict__"}:
            continue
        if isinstance(value, _FormProperty):
            fields.append((name, value.type))
            post_init_fns[name] = value.fn
            value = None
        namespace[name] = value

    fields = [
        (name, type_, namespace.pop(name)) if name in namespace else (name, type_)
        for name, type_ in fields
    ]

    dc = make_dataclass(
        cls.__name__, fields, bases=cls.__mro__[1:], namespace=namespace
    )
    _post_init_registry[dc] = post_init_fns
    return dc


def _is_classvar_type(type_):
    return (
        hasattr(type_, "__origin__")
        and getattr(type_, "__origin__") is ClassVar[Any].__origin__
    )


class _FormProperty:
    def __init__(self, fn):
        self.fn = fn

    @property
    def type(self):
        return getattr(self.fn, "__annotations__", {}).get("return", Any)


formProperty = _FormProperty


def sample(form, context=None):
    if context is None:
        context = get_root()

    if isinstance(form, Provider):
        return form.sample(context)
    elif not is_dataclass(form):
        return form

    x = deepcopy(form)
    context = context.subcontext(x.__class__.__name__)

    for field_def in fields(x):
        field_name = field_def.name
        field = getattr(x, field_name)
        if is_dataclass(field):
            value = sample(
                field, context.subcontext(field_name)
            )  # FIXME field vs class name?
            setattr(x, field_name, value)
        elif isinstance(field, Provider):
            value = field.sample(context.subcontext(field_name))
            setattr(x, field_name, value)

    if form.__class__ in _post_init_registry:
        for name, fn in _post_init_registry[form.__class__].items():
            setattr(x, name, sample(fn(x), context.subcontext(name)))
    return x
