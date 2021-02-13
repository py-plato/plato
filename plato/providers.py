from abc import ABC, abstractmethod


class Provider(ABC):
    @abstractmethod
    def sample(self, context):
        ...