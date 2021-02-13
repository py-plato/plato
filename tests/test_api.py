from dataclasses import field
import pytest

import plato
from plato import nested, Provider, shapeclass


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


def test_required_field():
    @shapeclass
    class TestData:
        field: str

    with pytest.raises(TypeError):
        TestData()

    assert TestData(field="foo").field == "foo"


def test_constant_field():
    @shapeclass
    class TestData:
        field: str = "value"

    assert TestData().field == "value"
    assert TestData("different value").field == "different value"


def test_generated_field():
    @shapeclass
    class TestData:
        field: str = FixedProvider()

    assert TestData().field == "provider value"
    assert TestData(field="different value").field == "different value"


def test_samples_generated_field_on_each_instantiation():
    @shapeclass
    class TestData:
        field: int = CountingProvider()

    assert TestData().field == 1
    assert TestData().field == 2


def test_nested_shapeclass():
    shared_counting_provider = CountingProvider()

    @shapeclass
    class Inner:
        field: int = shared_counting_provider

    @shapeclass
    class Outer:
        first: int = shared_counting_provider
        child: Inner = nested(Inner)
        last: int = shared_counting_provider

    outer = Outer()
    assert outer.child.field == 1
    assert outer.first == 2
    assert outer.last == 3


def test_context_provides_different_seeds_within_instance():
    @shapeclass
    class TestData:
        field0: bytes = SeedProvider()
        field1: bytes = SeedProvider()

    data = TestData()

    assert data.field0 != data.field1


def test_context_provides_different_seeds_across_instances():
    @shapeclass
    class TestData:
        field: bytes = SeedProvider()

    data = [TestData(), TestData()]

    assert data[0].field != data[1].field


def test_context_seeds_are_deterministic():
    @shapeclass
    class TestData:
        field0: bytes = SeedProvider()
        field1: bytes = SeedProvider()

    plato.seed(42)
    data0 = TestData()

    plato.seed(42)
    data1 = TestData()

    assert data0.field0 == data1.field0
    assert data0.field1 == data1.field1


def test_context_seeds_are_stable_against_field_removal():
    @shapeclass
    class TestData:
        field0: bytes = SeedProvider()
        field1: bytes = SeedProvider()

    plato.seed(42)
    field1_seed = TestData().field1

    @shapeclass
    class TestData:
        field1: bytes = SeedProvider()

    plato.seed(42)
    assert TestData().field1 == field1_seed


def test_context_seeds_for_nested_instances_are_independent_of_unnested_instances():
    @shapeclass
    class Inner:
        field: bytes = SeedProvider()

    @shapeclass
    class Outer:
        child: Inner = nested(Inner)

    plato.seed(42)
    Inner()
    seed = Outer().child.field

    plato.seed(42)
    assert Outer().child.field == seed
