import pytest

from plato.internal.graph import toposort


def test_toposort():
    graph = {
        0: (2, 3, 5),
        2: (5, 3),
        3: (4,),
        4: (),
        5: (),
    }
    valid_toposorts = {
        (4, 5, 3, 2, 0),
        (5, 4, 3, 2, 0),
    }

    assert graph == {
        0: (2, 3, 5),
        2: (5, 3),
        3: (4,),
        4: (),
        5: (),
    }
    assert tuple(toposort(graph)) in valid_toposorts


def test_toposort_with_cycle_raises():
    graph = {0: [1], 1: [0, 2], 2: []}

    with pytest.raises(ValueError):
        toposort(graph)


def test_toposort_on_empty_graph_returns_empty_list():
    assert toposort({}) == []
