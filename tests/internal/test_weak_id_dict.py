import weakref

import pytest

from plato.internal.weak_id_dict import WeakIdDict


class Dummy:
    pass


def test_missing_key():
    weak_id_dict = WeakIdDict()
    key = Dummy()

    assert key not in weak_id_dict
    with pytest.raises(KeyError):
        weak_id_dict[key]  # pylint: disable=pointless-statement

    with pytest.raises(KeyError):
        del weak_id_dict[key]


def test_setting_key():
    weak_id_dict = WeakIdDict()
    key = Dummy()

    weak_id_dict[key] = "value"
    assert key in weak_id_dict
    assert weak_id_dict[key] == "value"

    weak_id_dict[key] = "different-value"
    assert key in weak_id_dict
    assert weak_id_dict[key] == "different-value"

    different_key = Dummy()
    assert different_key not in weak_id_dict
    weak_id_dict[different_key] = "another-value"
    assert weak_id_dict[key] == "different-value"


def test_deleting_key():
    weak_id_dict = WeakIdDict()
    key = Dummy()

    weak_id_dict[key] = "value"
    del weak_id_dict[key]

    assert key not in weak_id_dict
    with pytest.raises(KeyError):
        weak_id_dict[key]  # pylint: disable=pointless-statement


def test_iterating_keys():
    weak_id_dict = WeakIdDict()
    keys = [Dummy() for i in range(4)]

    for k in keys:
        weak_id_dict[k] = "value"

    assert list(weak_id_dict) == keys
    assert len(weak_id_dict) == len(keys)


def test_keys_are_weak():
    weak_id_dict = WeakIdDict()
    key = Dummy()
    ref = weakref.ref(key)

    weak_id_dict[key] = "value"
    del key

    assert ref() is None
