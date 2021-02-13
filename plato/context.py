from collections import defaultdict
from dataclasses import dataclass, field
from hashlib import blake2b
from typing import Dict, Type


@dataclass(frozen=True)
class Context:
    seed: bytes


@dataclass(frozen=True)
class ProtoContext:
    hasher: blake2b
    type_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(lambda: 0))

    def subcontext(self, class_name: str) -> "ProtoContext":
        self.type_counts[class_name] += 1

        subhasher = self.hasher.copy()
        subhasher.update(class_name.encode())
        subhasher.update(_int2bytes(self.type_counts[class_name]))

        return ProtoContext(subhasher)

    def field_context(self, field_name: str) -> Context:
        field_hasher = self.hasher.copy()
        field_hasher.update(field_name.encode())
        return Context(seed=field_hasher.digest())

    @staticmethod
    def current() -> "ProtoContext":
        return _proto_context_stack[-1]

    def __enter__(self):
        _proto_context_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _proto_context_stack.pop()


def seed(value: int):
    # FIXME: should this verify that we are in the root context?
    _proto_context_stack[0] = ProtoContext(_create_hasher(value))


def _int2bytes(value: int) -> bytes:
    return value.to_bytes(value.bit_length() // 8 + 1, "big")


def _create_hasher(seed: int) -> blake2b:
    hasher = blake2b()
    hasher.update(_int2bytes(seed))
    return hasher


_proto_context_stack = [ProtoContext(_create_hasher(0))]