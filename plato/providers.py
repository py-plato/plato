from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    def sample(self, context):
        ...


class Shared(Provider):
    def __init__(self, provider):
        self.provider = provider

    def sample(self, context):
        if self not in context.metadata:
            context.metadata[self] = self.provider.sample(context)
        return context.metadata[self]
