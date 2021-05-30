import weakref

import pytest

from plato.internal.weak_id_dict import WeakIdDict


class Dummy:
    pass


def test_missing_key():
    d = WeakIdDict()
    key = Dummy()

    assert key not in d
    with pytest.raises(KeyError):
        d[key]

    with pytest.raises(KeyError):
        del d[key]


def test_setting_key():
    d = WeakIdDict()
    key = Dummy()

    d[key] = "value"
    assert key in d
    assert d[key] == "value"

    d[key] = "different-value"
    assert key in d
    assert d[key] == "different-value"

    different_key = Dummy()
    assert different_key not in d
    d[different_key] = "another-value"
    assert d[key] == "different-value"


def test_deleting_key():
    d = WeakIdDict()
    key = Dummy()

    d[key] = "value"
    del d[key]

    assert key not in d
    with pytest.raises(KeyError):
        d[key]


def test_iterating_keys():
    d = WeakIdDict()
    keys = [Dummy() for i in range(4)]

    for k in keys:
        d[k] = "value"

    assert list(d) == keys
    assert len(d) == len(keys)


def test_keys_are_weak():
    d = WeakIdDict()
    key = Dummy()
    ref = weakref.ref(key)

    d[key] = "value"
    del key

    assert ref() is None
