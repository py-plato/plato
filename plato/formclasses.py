from dataclasses import is_dataclass, make_dataclass, fields
from typing import Any, ClassVar
from weakref import WeakKeyDictionary

from .context import get_root_context
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
        if isinstance(value, _DerivedField):
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


class _DerivedField:
    def __init__(self, fn):
        self.fn = fn

    @property
    def type(self):
        return getattr(self.fn, "__annotations__", {}).get("return", Any)


derivedfield = _DerivedField


def sample(form, context=None):
    if context is None:
        context = get_root_context(form.__class__)

    if isinstance(form, Provider):
        return form.sample(context)
    elif not is_dataclass(form):
        return form

    field_values = {
        field_def.name: sample(
            getattr(form, field_def.name), context.subcontext(field_def.name)
        )
        for field_def in fields(form)
    }
    instance = form.__class__(**field_values)

    if form.__class__ in _post_init_registry:
        for name, fn in _post_init_registry[form.__class__].items():
            setattr(instance, name, sample(fn(instance), context.subcontext(name)))

    return instance
