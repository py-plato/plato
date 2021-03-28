"""Provider interface and base implemenations of functionality.

The members of this module are of interest if you are implementing your own
providers. Otherwise, you probably will not need them.

.. testsetup:: *

    from plato import sample
    from plato.context import Context
    from plato.providers.base import Provider, WithAttributeAccess
"""

from abc import ABC, abstractmethod
from typing import Any

from plato.context import Context


class Provider(ABC):
    """Provider interface."""

    @abstractmethod
    def sample(self, context: Context) -> Any:
        """Return a single value (sample) for the provider.

        Arguments
        ---------
        context: Context
            The sampling context. Use the random number generator from the
            context or initialize your random number generator from the seed
            provided in the context to ensure reproducibality.

        Returns
        -------
        Any
            The sampled value.
        """
        ...


class WithAttributeAccess:
    """Provider mixin to provide transparent access to attributes.

    Attributes existing on the implementing class and special members starting and
    ending with a double-underscore (``__``) are excluded.

    Example
    -------

    .. testcode:: WithAttributeAccess

        from dataclasses import dataclass

        @dataclass
        class Dto:
            foo: str = "foo"
            bar: str = "bar"

        class DtoProvider(Provider, WithAttributeAccess):
            def sample(self, context: Context) -> Dto:
                return Dto()

        print(sample(DtoProvider().foo))

    .. testoutput:: WithAttributeAccess

        foo
    """

    def __getattr__(self, field_name: str):
        if field_name.startswith("__") and field_name.endswith("__"):
            raise AttributeError
        return AttributeProvider(self, field_name)


class AttributeProvider(Provider, WithAttributeAccess):
    """Provider of an attribute of the samples of another provider.

    Arguments
    ---------
    parent: Provider
        Parent provider to sample.
    attr_name: str
        Name of the attribute to provide from the sampled object.
    """

    def __init__(self, parent: Provider, attr_name: str):
        self.parent = parent
        self.attr_name = attr_name

    def sample(self, context: Context) -> Any:
        from ..formclasses import sample

        return getattr(sample(self.parent, context), self.attr_name)
