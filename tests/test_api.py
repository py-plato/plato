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


class CollectSeedsProvider(Provider):
    def __init__(self):
        self.seeds = []

    def sample(self, context):
        self.seeds.append(context.seed)


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
    provider = CollectSeedsProvider()

    @shapeclass
    class TestData:
        field0: None = provider
        field1: None = provider

    TestData()

    assert provider.seeds[0] != provider.seeds[1]


def test_context_provides_different_seeds_across_instances():
    @shapeclass
    class TestData:
        field: None = CollectSeedsProvider()

    TestData()
    TestData()

    assert TestData.field.seeds[0] != TestData.field.seeds[1]


def test_context_seeds_are_deterministic():
    provider = CollectSeedsProvider()

    @shapeclass
    class TestData:
        field0: None = provider
        field1: None = provider

    plato.seed(42)
    TestData()
    seeds_first_run = list(provider.seeds)
    provider.seeds.clear()

    plato.seed(42)
    TestData()

    assert seeds_first_run == provider.seeds


def test_context_seeds_are_stable_against_field_removal():
    provider = CollectSeedsProvider()

    @shapeclass
    class TestData:
        field0: None = provider
        field1: None = provider

    plato.seed(42)
    TestData()
    field1_seed = provider.seeds[1]
    provider.seeds.clear()

    @shapeclass
    class TestData:
        field1: None = provider

    plato.seed(42)
    TestData()

    assert provider.seeds[0] == field1_seed