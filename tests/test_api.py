import pytest

from plato import shapeclass


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