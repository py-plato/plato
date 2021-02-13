import pytest

from plato import nested, Provider, shapeclass


class FixedProvider(Provider):
    def sample(self):
        return "provider value"


class CountingProvider(Provider):
    count: int = 0

    def sample(self):
        self.count += 1
        return self.count


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
