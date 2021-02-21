from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    def sample(self, context):
        ...

    def __getattr__(self, field_name: str):
        return FieldProvider(self, field_name)


class FieldProvider(Provider):
    def __init__(self, parent: Provider, field_name: str):
        self.parent = parent
        self.field_name = field_name

    def sample(self, context):
        from ..shapeclasses import sample

        return getattr(sample(self.parent, context), self.field_name)


class Shared(Provider):
    def __init__(self, provider):
        self.provider = provider
        self._sampled = False
        self._value = None

    def sample(self, context):
        from ..shapeclasses import sample

        if not self._sampled:
            self._value = sample(self.provider, context)
            self._sampled = True
        return self._value