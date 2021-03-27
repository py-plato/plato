from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    def sample(self, context):
        ...


class WithFieldAccess:
    def __getattr__(self, field_name: str):
        if field_name.startswith("__") and field_name.endswith("__"):
            raise AttributeError
        return FieldProvider(self, field_name)


class FieldProvider(Provider, WithFieldAccess):
    def __init__(self, parent: Provider, field_name: str):
        self.parent = parent
        self.field_name = field_name

    def sample(self, context):
        from ..formclasses import sample

        return getattr(sample(self.parent, context), self.field_name)


class Shared(Provider, WithFieldAccess):
    def __init__(self, provider):
        self.provider = provider

    def sample(self, context):
        from ..formclasses import sample

        if self not in context.parent.meta:
            context.parent.meta[self] = sample(self.provider, context)

        return context.parent.meta[self]