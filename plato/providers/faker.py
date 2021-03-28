"""Support for using the `Faker <https://faker.readthedocs.io/en/master/>`_
library with Plato.
"""

from functools import partial

from faker import Faker  # type: ignore

from .base import Provider


class FromFaker:
    """Create a `.Provider` from a :doc:`Faker <fakerclass>` instance.

    All indexing operations and attribute access will be delegated to to the
    :doc:`Faker <fakerclass>` instance, but return `.Provider` instances usable
    in a `.formclass`.

    Arguments
    ---------
    faker: Faker, optional
        Faker instance used to generate values. If not given a new instance
        using the default will be created.

    Example
    -------

    .. testsetup:: FromFaker

        import plato
        from faker import Faker
        from plato import sample
        from plato.providers.faker import FromFaker

        plato.seed(0)

    .. testcode:: FromFaker

        fake = FromFaker(Faker(["en-US", "de-DE"]))

        print(sample(fake["en-US"].street_address()))
        print(sample(fake["de-DE"].street_address()))

    .. testoutput:: FromFaker

        413 Perez Cape Apt. 615
        Schaafallee 41

    """

    def __init__(self, faker=None):
        if faker is None:
            faker = Faker()
        self.faker = faker

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError
        return partial(_FakerMethodProvider, self.faker, getattr(self.faker, name))

    def __getitem__(self, key):
        return FromFaker(self.faker[key])


class _FakerMethodProvider(Provider):
    def __init__(self, faker, method, *args, **kwargs):
        self.faker = faker
        self.method = method
        self.args = args
        self.kwargs = kwargs

    def sample(self, context):
        self.faker.seed_instance(context.seed)
        return self.method(*self.args, **self.kwargs)
