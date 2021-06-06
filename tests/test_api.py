"""Tests of the Plato's public core API."""

import typing
from dataclasses import dataclass, fields

import pytest

import plato
from plato import Provider, Shared, formclass, sample
from plato.formclasses import InitVar, derivedfield
from plato.providers.base import ProviderProtocol, WithAttributeAccess


class FixedProvider(Provider):
    def sample(self, _context):
        return "provider value"


class CountingProvider(Provider):
    count: int = 0

    def sample(self, _context):
        self.count += 1
        return self.count


class SeedProvider(Provider):
    def sample(self, context):
        return context.seed


class SequenceProvider(Provider, WithAttributeAccess):
    def __init__(self, values):
        self.values = values
        self._n_values_sampled = 0

    def sample(self, context):  # pylint: disable=unused-argument
        retval = self.values[self._n_values_sampled % len(self.values)]
        self._n_values_sampled += 1
        return retval


def test_required_field():
    @formclass
    class TestData:
        field: str

    with pytest.raises(TypeError):
        sample(TestData())

    assert sample(TestData(field="foo")).field == "foo"


def test_default_field():
    @formclass
    class TestData:
        field: str = "value"

    assert sample(TestData()).field == "value"
    assert sample(TestData("different value")).field == "different value"


def test_generated_field():
    @formclass
    class TestData:
        field: str = FixedProvider()

    assert sample(TestData()).field == "provider value"
    assert sample(TestData(field="different value")).field == "different value"


def test_samples_generated_field_on_each_instantiation():
    @formclass
    class TestData:
        field: int = CountingProvider()

    assert sample(TestData()).field == 1
    assert sample(TestData()).field == 2


def test_ignores_class_variables():
    @formclass
    class TestData:
        class_var0 = CountingProvider()
        class_var1: typing.ClassVar[CountingProvider] = CountingProvider()

    assert sample(TestData()).class_var0.count == 0
    assert sample(TestData()).class_var1.count == 0


def test_keeps_namespace():
    @formclass
    class TestData:
        def some_method(self):
            return "some_method"

        @property
        def some_property(self):
            return "some_property"

    data = sample(TestData())
    assert data.some_method() == "some_method"
    assert data.some_property == "some_property"


def test_nested_formclass():
    shared_counting_provider = CountingProvider()

    @formclass
    class Inner:
        field: int = shared_counting_provider

    @formclass
    class Outer:
        first: int = shared_counting_provider
        child: Inner = Inner()
        last: int = shared_counting_provider

    outer = sample(Outer())
    assert outer.first == 1
    assert outer.child.field == 2
    assert outer.last == 3


def test_context_provides_different_seeds_within_instance():
    @formclass
    class TestData:
        field0: bytes = SeedProvider()
        field1: bytes = SeedProvider()

    data = sample(TestData())

    assert data.field0 != data.field1


def test_context_provides_different_seeds_across_instances():
    @formclass
    class TestData:
        field: bytes = SeedProvider()

    data = [sample(TestData()), sample(TestData())]

    assert data[0].field != data[1].field


def test_context_seeds_are_deterministic():
    @formclass
    class TestData:
        field0: bytes = SeedProvider()
        field1: bytes = SeedProvider()

    plato.seed(42)
    data0 = sample(TestData())

    plato.seed(42)
    data1 = sample(TestData())

    assert data0.field0 == data1.field0
    assert data0.field1 == data1.field1


def test_context_seeds_are_stable_against_field_removal():
    @formclass
    class TestData:
        field0: bytes = SeedProvider()
        field1: bytes = SeedProvider()

    plato.seed(42)
    field1_seed = sample(TestData()).field1

    @formclass
    class TestData:  # pylint: disable=function-redefined
        field1: bytes = SeedProvider()

    plato.seed(42)
    assert sample(TestData()).field1 == field1_seed


def test_context_seeds_for_nested_instances_are_independent_of_unnested_instances():
    @formclass
    class Inner:
        field: bytes = SeedProvider()

    @formclass
    class Outer:
        child: Inner = Inner()

    plato.seed(42)
    Inner()
    seed = sample(Outer()).child.field

    plato.seed(42)
    assert sample(Outer()).child.field == seed


def test_derived_and_nested_formclass_behaviour():
    @formclass
    class Inner:
        field0: str = "field0"
        field1: str = "field1"

    @formclass
    class Outer:
        @formclass
        class InnerWithChangedDefault(Inner):
            field1: str = FixedProvider()

        child: Inner = InnerWithChangedDefault()

    outer_default = sample(Outer())
    assert outer_default.child.field0 == "field0"
    assert outer_default.child.field1 == "provider value"

    outer_base_inner = sample(Outer(child=Inner()))
    assert outer_base_inner.child.field0 == "field0"
    assert outer_base_inner.child.field1 == "field1"

    outer_derived_inner = sample(Outer(child=Outer.InnerWithChangedDefault()))
    assert outer_derived_inner.child.field0 == "field0"
    assert outer_derived_inner.child.field1 == "provider value"

    outer_non_default_derived_inner = sample(
        Outer(child=Outer.InnerWithChangedDefault(field1="non default"))
    )
    assert outer_non_default_derived_inner.child.field0 == "field0"
    assert outer_non_default_derived_inner.child.field1 == "non default"


def test_override_with_provider():
    @formclass
    class TestData:
        field: str = "foo"

    assert sample(TestData(field=FixedProvider())).field == "provider value"


def test_shared_values():
    @formclass
    class TestData:
        shared_data = Shared(CountingProvider())
        field0: int = shared_data
        field1: int = shared_data

    data = sample(TestData())
    assert data.field0 == 1
    assert data.field1 == 1

    @formclass
    class TestData:  # pylint: disable=function-redefined
        field0: int = Shared(CountingProvider())
        field1: int = field0

    data = sample(TestData())
    assert data.field0 == 1
    assert data.field1 == 1


def test_different_shared_values_are_independent():
    @formclass
    class TestData:
        provider = CountingProvider()
        field0: int = Shared(provider)
        field1: int = Shared(provider)

    data = sample(TestData())
    assert data.field0 == 1
    assert data.field1 == 2


def test_shared_values_are_independent_across_instances():
    provider = CountingProvider()

    @formclass
    class TestData:
        field: int = Shared(provider)

    assert sample(TestData()).field != sample(TestData()).field


def test_shared_values_are_also_shared_in_subinstance():
    @formclass
    class Inner:
        field: int

    @formclass
    class Outer:
        field: int = Shared(CountingProvider())
        child: Inner = Inner(field)

    data = sample(Outer())
    assert data.field == data.child.field


def test_shared_values_are_independent_across_different_field_instances():
    @formclass
    class Inner:
        field: int = Shared(CountingProvider())

    @formclass
    class Outer:
        child0: Inner = Inner()
        child1: Inner = Inner()

    data = sample(Outer())
    assert data.child0.field != data.child1.field


def test_nonshared_dataclass_field_access():
    @dataclass
    class Data:
        field0: str
        field1: str

    @formclass
    class TestData:
        child = SequenceProvider([Data("a0", "a1"), Data("b0", "b1")])
        field0: str = child.field0
        field1: str = child.field1

    test_data = sample(TestData())
    assert test_data.field0 == "a0"
    assert test_data.field1 == "b1"


def test_shared_dataclass_field_access():
    @dataclass
    class Data:
        field0: str
        field1: str

    @formclass
    class TestData:
        child = Shared(
            SequenceProvider(
                [Data(field0="a0", field1="a1"), Data(field0="b0", field1="b1")]
            )
        )
        field0: str = child.field0
        field1: str = child.field1

    test_data = sample(TestData())
    assert test_data.field0 == "a0"
    assert test_data.field1 == "a1"


def test_nonshared_formclass_field_access():
    @formclass
    class Inner:
        provider = SequenceProvider(list(range(6)))
        field0: str = provider
        field1: str = provider

    @formclass
    class TestData:
        child = Inner()
        field0a: str = child.field0
        field0b: str = child.field0
        field1: str = child.field1

    test_data = sample(TestData())
    assert test_data.field0a == 0
    assert test_data.field0b == 1
    assert test_data.field1 == 2


def test_shared_formclass_field_access():
    @formclass
    class Inner:
        provider = SequenceProvider(list(range(6)))
        field0: str = provider
        field1: str = provider

    @formclass
    class TestData:
        child = Shared(Inner())
        field0a: str = child.field0
        field0b: str = child.field0
        field1: str = child.field1

    test_data = sample(TestData())
    assert test_data.field0a == 0
    assert test_data.field0b == 0
    assert test_data.field1 == 1


def test_derivedfield():
    @formclass
    class TestData:
        field: str = "default"

        @derivedfield
        def derived(self, field) -> str:
            return field

    field_map = {f.name: f.type for f in fields(TestData)}
    assert field_map["derived"] == str
    assert sample(TestData(field="actual")).derived == "actual"


def test_derivedfield_with_provider():
    @formclass
    class TestData:
        @derivedfield
        def derived(self) -> ProviderProtocol[str]:
            return FixedProvider()

    field_map = {f.name: f.type for f in fields(TestData)}
    assert field_map["derived"] == str
    assert sample(TestData()).derived == "provider value"


def test_derivedfield_with_formclass():
    @formclass
    class Derived:
        field: str = FixedProvider()

    @formclass
    class TestData:
        @derivedfield
        def derived(self) -> Derived:
            return Derived()

    field_map = {f.name: f.type for f in fields(TestData)}
    assert field_map["derived"] == Derived
    assert sample(TestData()).derived.field == "provider value"


def test_overwrite_derivedfield():
    @formclass
    class TestData:
        @derivedfield
        def derived(self) -> str:
            "derived value"

    assert sample(TestData(derived="provided value")).derived == "provided value"


def test_derivedfield_initialization_order():
    @formclass
    class TestData:
        @derivedfield
        def derived2(self, derived0, derived1) -> int:
            return derived1 + derived0

        @derivedfield
        def derived0(self) -> int:
            return 1

        @derivedfield
        def derived1(self, derived0) -> int:
            return derived0 + 1

        @derivedfield
        def derived4(self, derived2, derived3) -> int:
            return derived3 + derived2

        @derivedfield
        def derived3(self, derived1, derived2) -> int:
            return derived2 + derived1

    assert sample(TestData()).derived4 == 8


def test_initvar_not_included_in_fields():
    @formclass
    class TestData:
        field: InitVar[str]

    assert "field" not in fields(sample(TestData(field="data")))


def test_initvar_is_passed_to_derivedfields():
    @formclass
    class TestData:
        base_value: InitVar[int]

        @derivedfield
        def plus_one(self, base_value) -> int:
            return base_value + 1

    assert sample(TestData(base_value=1)).plus_one == 2
