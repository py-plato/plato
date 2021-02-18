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
        return getattr(self.parent.sample(context), self.field_name)


class Shared(Provider):
    def __init__(self, provider):
        self.provider = provider

    def sample(self, context):
        if self not in context.metadata:
            context.metadata[self] = self.provider.sample(context)
        return context.metadata[self]
