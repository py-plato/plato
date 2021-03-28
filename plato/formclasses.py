"""Implementation of Plato's core formclasses API.

Plato's core API consists out of

* the `.formclass` decorator to annotate classes defining the hierarchical
  structure of desired test data,
* and the `.sample` function to generate instances of concrete test data from
  instances of such form classes.

.. testsetup:: *

    from plato import formclass, sample
    import plato.providers.faker

    plato.seed(0)
"""

from dataclasses import fields, is_dataclass, make_dataclass
from typing import Any, Callable, ClassVar, Dict, Mapping
from weakref import WeakKeyDictionary

from .context import get_root_context
from .providers.base import Provider, ProviderProtocol

_post_init_registry: Mapping[
    object, Dict[str, Callable[[object], Any]]
] = WeakKeyDictionary()


def formclass(cls):
    """Class decorator to process a class definition as formclass.

    The *formclass* decorator is one of the main parts of the Plato API. A class
    annotated with it will be processed to enable Plato's feature. In
    particular, it will become a :func:`~dataclasses.dataclass` and support
    for the `.derivedfield` decorator will be added.

    Similar to a :func:`~dataclasses.dataclass`, you can define fields in
    a *formclass* using type annotations. In addition to normal default values
    and :func:`~dataclasses.field` assignments, you can assign a `.Provider`
    that is used to generate values when using `.sample`.

    Example
    -------

    .. testcode:: formclass

        fake = plato.providers.faker.FromFaker()

        @formclass
        class MyFormclass:
            field: str = "value"
            generated_field: str = fake.first_name()

        data = sample(MyFormclass())
        print(data.field)
        print(data.generated_field)

    .. testoutput:: formclass

        value
        Alicia

    ..
        # noqa: DAR101 cls
        # noqa: DAR201 return
    """

    post_init_fns = {}

    annotations = getattr(cls, "__annotations__", {})
    instance_fields = [
        (name, type_)
        for name, type_ in annotations.items()
        if not _type_origin_matches(type_, ClassVar[Any])
    ]

    namespace = {}
    for name, value in cls.__dict__.items():
        if name in {"__annotations__", "__dict__"}:
            continue
        if isinstance(value, _DerivedField):
            instance_fields.append((name, value.type))
            post_init_fns[name] = value.fn
            value = None
        namespace[name] = value

    instance_fields = [
        (name, type_, namespace.pop(name)) if name in namespace else (name, type_)
        for name, type_ in instance_fields
    ]

    dc = make_dataclass(
        cls.__name__, instance_fields, bases=cls.__mro__[1:], namespace=namespace
    )
    _post_init_registry[dc] = post_init_fns
    return dc


def _type_origin_matches(annotation, type_):
    return (
        hasattr(annotation, "__origin__")
        and getattr(annotation, "__origin__") is type_.__origin__
    )


class _DerivedField:
    """Method decorator to derive a `.formclass` field from other fields.

    When instantiating a `.formclass`, the decorated method will be run after
    initializing all normal fields. The returned value will be used to add
    a field with the method's name to the `.formclass` instance.

    When multiple methods are decorated with *derivedfield*, they run in order
    of declaration.

    Attributes
    ----------
    fn: func
        Decorated method.
    """

    def __init__(self, fn):
        self.fn = fn

    @property
    def type(self):
        """Type annotation of the derived field."""
        annotation = getattr(self.fn, "__annotations__", {}).get("return", Any)
        if _type_origin_matches(annotation, ProviderProtocol[Any]):
            annotation = annotation.__args__[0]
        return annotation


# pylint: disable=invalid-name
derivedfield = _DerivedField


def sample(form, context=None):
    """Generates a dataclass with concrete values from a `.formclass` instance.

    Recursively processes a `.formclass` instance and returns an analogous
    :func:`~dataclasses.dataclass` where all `.Provider` have been replaced
    with values generated from these providers. The returned
    `~dataclasses.dataclass` will also have fields added for `.derivedfield`
    annotated methods.

    This function uses a context to provide deterministic random number seeds
    based on the field names and allow information to be shared between
    `.Provider` instances. Usually it will not be necessary to provide this
    context as it will be automatically initialized for each top-level
    invocation.

    Arguments
    ---------
    form: object
        Usually a `.formclass` instance to be processed. But can also be a
        `.Provider` instance which will forward the call to the provider's
        `.Provider.sample` method. Any other type of object will be returned
        unchanged.
    context: Context, optional
        Context of the sample operation, for example, the random number seed to
        use. Usually this argument has not to be set manually and will be
        initialized automatically.

    Returns
    -------
    object
        For a `.formclass` a `~dataclasses.dataclass` instance is returned
        with `.Provider` instances replaced by sampled values and
        `.derviedfield` methods added as fields. For a `.Provider` the sampled
        value will be returned and for all other objects, the object itself
        is returned.

    Examples
    --------

    With `.formclass`:

    .. testcode:: sample

        fake = plato.providers.faker.FromFaker()

        @formclass
        class MyFormclass:
            field: str = "value"
            generated_field: str = fake.first_name()

        data = sample(MyFormclass())
        print(data.field)
        print(data.generated_field)

    .. testoutput:: sample

        value
        Alicia

    With `.Provider`:

    .. testcode:: sample

        fake = plato.providers.faker.FromFaker()
        print(sample(fake.first_name()))

    .. testoutput:: sample

        Thomas

    Any other object:

    .. testcode:: sample

        print(sample("foo"))

    .. testoutput:: sample

        foo

    """

    if context is None:
        context = get_root_context(form.__class__)

    if isinstance(form, Provider):
        return form.sample(context)
    if not is_dataclass(form):
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
            value = getattr(instance, name, None)
            if value is None:
                value = fn(instance)
            setattr(instance, name, sample(value, context.subcontext(name)))

    return instance
