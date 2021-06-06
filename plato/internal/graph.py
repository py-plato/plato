"""Graph algorithms used in Plato."""

from typing import Collection, Dict, Mapping, Set, TypeVar

T = TypeVar("T")


def toposort(graph: Mapping[T, Collection[T]]) -> Collection[T]:
    """Returns the topological sort of ``graph``.

    Arguments
    ---------
    graph
        A mapping to the dependencies of a vertex that need to
        be sorted prior to a vertex.

    Returns
    -------
    The topological sort of ``graph``, i.e. the keys in ``graph`` in the order
    they need to be processed to always have all necessary dependencies
    available when processing a particular key.

    Raises
    ------
    ValueError
        If the ``graph`` contains a cycle and thus no topological sorting
        exists.
    """

    remaining_graph = {vertex: set(edges) for vertex, edges in graph.items()}

    toposorted = []
    dependencies_fulfilled = set(
        vertex for vertex, edges in graph.items() if len(edges) == 0
    )

    dependents: Dict[T, Set[T]] = {vertex: set() for vertex in graph}
    for vertex, edges in graph.items():
        for edge in edges:
            dependents[edge].add(vertex)

    while dependencies_fulfilled:
        vertex = dependencies_fulfilled.pop()
        toposorted.append(vertex)

        for dependent in dependents[vertex]:
            remaining_graph[dependent].remove(vertex)
            if len(remaining_graph[dependent]) == 0:
                dependencies_fulfilled.add(dependent)

    if any(len(edges) > 0 for edges in remaining_graph.values()):
        raise ValueError("The graph must not contain cycles.")

    return toposorted
