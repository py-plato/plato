from dataclasses import field, Field
from typing import Type

from .providers import Provider


def nested(provider_cls: Type[Provider]) -> Field:
    return field(default_factory=provider_cls)