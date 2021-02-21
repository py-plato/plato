from copy import deepcopy
from functools import partial

from faker import Faker

from .base import Provider


class FromFaker:
    def __init__(self, faker=None):
        if faker is None:
            faker = Faker()
        self.faker = faker

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError
        return partial(FakerMethodProvider, self.faker, getattr(self.faker, name))

    def __getitem__(self, key):
        return FromFaker(self.faker[key])

    def __deepcopy__(self, memo):
        return FromFaker(self.faker)


class FakerMethodProvider(Provider):
    def __init__(self, faker, method, *args, **kwargs):
        self.faker = faker
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def sample(self, context):
        self.faker.seed_instance(context.seed)
        return self.method(*self.args, **self.kwargs)

    def __deepcopy__(self, memo):
        return FakerMethodProvider(
            self.faker,
            self.method,
            *deepcopy(self.args, memo),
            **deepcopy(self.kwargs, memo),
        )
