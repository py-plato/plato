import pytest

from plato import Provider, shapeclass


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
    class FixedProvider(Provider):
        def sample(self):
            return "provider value"

    @shapeclass
    class TestData:
        field: str = FixedProvider()

    assert TestData().field == "provider value"
    assert TestData(field="different value").field == "different value"