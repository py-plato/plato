"""Commonly used providers."""

from typing import Any

from ..context import Context
from ..formclasses import sample
from .base import Provider, WithAttributeAccess


class Shared(Provider, WithAttributeAccess):
    """Share the sampled value of a Provider across multiple fields.

    Try to avoid sharing values across more than a single `.formclass` because
    the semantics of *Shared* are a bit unintuitive in other cases. But for
    completeness sake, this is how it works: the first sampled value is reused
    within the same `.formclass` instance and old child instances. However,
    if the value is first sampled in a child instance, it will not be reused
    in the parent instance.

    Arguments
    ---------
    provider: Provider
        Provider to share sampled values of.

    Examples
    --------
    Normal usage:

    .. testsetup:: Shared

        from plato import formclass, sample
        from plato.providers.base import Provider
        from plato.providers.common import Shared

    .. testcode:: Shared

        from dataclasses import asdict
        from pprint import pprint

        class CountingProvider(Provider):
            def __init__(self):
                self.n = 0

            def sample(self, context: Context) -> int:
                self.n += 1
                return self.n

        counting_provider = CountingProvider()

        @formclass
        class MyFormclass:
            shared: int = Shared(counting_provider)
            same: int = shared
            different: int = counting_provider

        pprint(asdict(sample(MyFormclass())))

    .. testoutput:: Shared

        {'different': 2, 'same': 1, 'shared': 1}

    Discouraged use across multiple `.formclass` instances:

    .. testcode:: Shared

        counting_provider = CountingProvider()

        @formclass
        class Child:
            value: int = Shared(counting_provider)

        @formclass
        class Parent:
            samples_child_first: Child = Child()
            samples_new_value_in_parent: int = samples_child_first.value
            reuses_value_sampled_in_parent: Child = Child()

        pprint(asdict(sample(Parent())))

    .. testoutput:: Shared

        {'reuses_value_sampled_in_parent': {'value': 2},
         'samples_child_first': {'value': 1},
         'samples_new_value_in_parent': 2}

    """

    def __init__(self, provider: Provider):
        self.provider = provider

    def sample(self, context: Context) -> Any:
        if context.parent is None:
            raise ValueError("Subcontext with set parent required.")

        if self not in context.parent.meta:
            context.parent.meta[self] = sample(self.provider, context)

        return context.parent.meta[self]
