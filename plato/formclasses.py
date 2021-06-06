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

import inspect
import sys
from dataclasses import Field, InitVar, fields, is_dataclass, make_dataclass
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    FrozenSet,
    Generic,
    List,
    MutableMapping,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)
from weakref import WeakKeyDictionary

from .context import Context, get_root_context
from .internal.graph import toposort
from .internal.weak_id_dict import WeakIdDict
from .providers.base import Provider, ProviderProtocol

_init_var_registry: WeakIdDict[Dict[str, Any]] = WeakIdDict()
_post_init_registry: MutableMapping[
    object, Dict[str, Callable[..., Any]]
] = WeakKeyDictionary()


T = TypeVar("T")


def formclass(cls: type) -> type:
    """Class decorator to process a class definition as formclass.

    The *formclass* decorator is one of the main parts of the Plato API. A class
    annotated with it will be processed to enable Plato's feature. In
    particular, it will become a :func:`~dataclasses.dataclass` and support
    for the `.derivedfield` decorator will be added.

    Similar to a :func:`~dataclasses.dataclass`, you can define fields in
    a *formclass* using type annotations. In addition to normal default values
    and :func:`~dataclasses.field` assignments, you can assign a `.Provider`
    that is used to generate values when using `.sample`.

    Like `~dataclasses`, a *formclass* supports the `InitVar` type. A field
    with such a type will not be available on the instance, but will be passed
    as argument to the `__post_init__` method (in order of declaration) and
    `.derivedfield` methods (as keyword argument by name).

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

    post_init_fns: Dict[str, Callable[..., Any]] = {}

    annotations = getattr(cls, "__annotations__", {})
    instance_fields = [
        (name, type_)
        for name, type_ in annotations.items()
        if not _type_origin_matches(type_, ClassVar[Any])
    ]

    namespace: Dict[str, Any] = {}
    for name, value in cls.__dict__.items():
        if name in {"__annotations__", "__dict__"}:
            continue
        if isinstance(value, _DerivedField):
            instance_fields.append((name, value.type))
            post_init_fns[name] = value.fn
            value = None
        namespace[name] = value

    orig_post_init = namespace.get("__post_init__", None)
    init_var_names = [
        name for name, type_ in annotations.items() if _is_init_var(type_)
    ]

    def __post_init__(self: Any, *args: Any) -> None:
        _init_var_registry[self] = dict(zip(init_var_names, args))
        if orig_post_init:
            orig_post_init(self, *args)

    namespace["__post_init__"] = __post_init__

    instance_fields_with_field_def: List[
        Union[Tuple[str, type], Tuple[str, type, Field]]
    ] = [
        (name, type_, cast(Field, namespace.pop(name)))
        if isinstance(namespace.get(name, None), Field)
        else (name, type_)
        for name, type_ in instance_fields
    ]

    dc = make_dataclass(
        cls.__name__,
        instance_fields_with_field_def,
        bases=cls.__mro__[1:],
        namespace=namespace,
    )
    _post_init_registry[dc] = post_init_fns
    return dc


def _type_origin_matches(annotation: Type, type_: object) -> bool:
    return hasattr(annotation, "__origin__") and getattr(
        annotation, "__origin__"
    ) is getattr(type_, "__origin__", None)


def _is_init_var(type_: type) -> bool:
    is_py37_init_var = (
        sys.version_info[:2] <= (3, 7) and type_.__class__ is InitVar.__class__
    )
    return is_py37_init_var or isinstance(type_, InitVar)


DerivedFieldT = TypeVar("DerivedFieldT", bound=Callable)


class _DerivedField(Generic[DerivedFieldT]):
    """Method decorator to derive a `.formclass` field from other fields.

    When instantiating a `.formclass`, the decorated method will be run after
    initializing all normal fields. The returned value will be used to add
    a field with the method's name to the `.formclass` instance. You get
    access to your fields (including `InitVar` fields) by declaring additional
    arguments for the `.derivedfield` using the same name as the field.

    Attributes
    ----------
    fn
        Decorated method.
    """

    def __init__(self, fn: DerivedFieldT):
        self.fn = fn

    @property
    def type(self) -> Type:
        """Type annotation of the derived field."""
        annotation = getattr(self.fn, "__annotations__", {}).get("return", Any)
        if _type_origin_matches(annotation, ProviderProtocol[Any]):
            annotation = annotation.__args__[0]
        return annotation


# pylint: disable=invalid-name
derivedfield = _DerivedField


def sample(form: T, context: Context = None) -> T:
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
    form
        Usually a `.formclass` instance to be processed. But can also be a
        `.Provider` instance which will forward the call to the provider's
        `.Provider.sample` method. Any other type of object will be returned
        unchanged.
    context
        Context of the sample operation, for example, the random number seed to
        use. Usually this argument has not to be set manually and will be
        initialized automatically.

    Returns
    -------
    T
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

    init_args = dict(_init_var_registry[form])
    init_args.update(
        {
            field_def.name: sample(
                getattr(form, field_def.name), context.subcontext(field_def.name)
            )
            for field_def in fields(form)
        }
    )
    instance = form.__class__(**init_args)  # type: ignore[call-arg]

    if form.__class__ in _post_init_registry:

        def get_post_init_arg(name: str) -> Any:
            if name in _init_var_registry[form]:
                return _init_var_registry[form][name]
            return getattr(instance, name)

        dependency_graph: Dict[str, FrozenSet[str]] = {
            name: frozenset() for name in init_args
        }
        for name, fn in _post_init_registry[form.__class__].items():
            parameter_iter = iter(inspect.signature(fn).parameters)
            next(parameter_iter)  # skip self
            dependency_graph[name] = frozenset(parameter_iter)

        eval_order = toposort(dependency_graph)

        for name in eval_order:
            if name in _init_var_registry[form]:
                continue

            value = getattr(instance, name, None)
            if value is not None:
                continue

            fn = _post_init_registry[form.__class__][name]
            init_var_args = {
                name: get_post_init_arg(name) for name in dependency_graph[name]
            }
            value = fn(instance, **init_var_args)
            setattr(instance, name, sample(value, context.subcontext(name)))

    return instance
