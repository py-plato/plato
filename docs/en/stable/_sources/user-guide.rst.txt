User Guide
==========

.. testsetup:: *

    import plato
    from plato import derivedfield, formclass, sample, Shared
    from plato.providers.faker import FromFaker

    plato.seed(0)
    fake = FromFaker()

Defining formclasses
--------------------

In Plato you define
the hierarchical structure of the test data to generate
with classes using the `.formclass` decorator.
This is similar to Python's :py:mod:`dataclasses`.
In fact,
a class decorated with `.formclass`
will be converted to a special :py:func:`~dataclasses.dataclass`.

Like in :py:mod:`dataclasses`,
you define fields on the `.formclass`
using type annotations
and optionally default values::

    @formclass
    class MyFormclass:
        mandatory_field: str
        constant_field: int = 42
        generated_field: str = fake.first_name()
        
In the following,
declaring different types of fields is discussed.


Mandatory fields
^^^^^^^^^^^^^^^^

For mandatory fields a value must be provided
when instantiating the `.formclass`.
To make a field mandatory,
skip the default value assignment
in the field declaration.

.. testcode::

    @formclass
    class MyFormclass:
        mandatory_field: str

    MyFormclass(mandatory_field="the value")  # OK

    MyFormclass()  # but this raises
    
.. testoutput::

    Traceback (most recent call last):
        ...
    TypeError: __init__() missing 1 required positional argument: 'mandatory_field'


Constant fields
^^^^^^^^^^^^^^^

By assigning a constant default value in a field declaration,
the field becomes optional on instantiation.
It will be initialized with the provided value
if not given,
but can be overwritten
with a different value.

.. testcode::

    @formclass
    class MyFormclass:
        constant_field: str = "default value"

    print(MyFormclass().constant_field)
    print(MyFormclass(constant_field="different value").constant_field)
    
.. testoutput::

    default value
    different value


Generated fields
^^^^^^^^^^^^^^^^

Mandatory and constant fields do not really add anything
over standard :py:mod:`dataclasses`.
The benefit of Plato is
that it allows you to also assign `.providers`
to have data generated dynamically.

In the following example we will use the `.FromFaker` provider
that exposes the API of the `Faker <https://faker.readthedocs.io/en/latest/>`_
library for generating basic values.

.. testcode::

    from plato.providers.faker import FromFaker

    fake = FromFaker()

    @formclass
    class MyFormclass:
        generated_field: str = fake.first_name()
        
When instantiating this formclass,
it will have the provider instance assigned to the field:

.. testcode::

    print(MyFormclass().generated_field)

.. testoutput::

    <plato.providers.faker._FakerMethodProvider object at 0x...>
    
To get an instance
with actual generated values,
use the `~plato.formclasses.sample()` function:

.. testcode::

    print(sample(MyFormclass()).generated_field)

.. testoutput::

    Alicia

It is possible to overwrite providers
with either constant values
or different providers:

.. testcode::

    print(sample(MyFormclass(
        generated_field="fixed value"
    )).generated_field)

    print(sample(MyFormclass(
        generated_field=fake.postcode()
    )).generated_field)
    
.. testoutput::

    fixed value
    16000

The power of Plato is
that a `.formclass` instance happens to be also a provider.
Thus,
a hierachical structure can be declared
and the data is generated accordingly.

.. testcode::

    @formclass
    class ComposedClass:
        field0: MyFormclass = MyFormclass()
        field1: MyFormclass = MyFormclass()
        field_with_postcode: MyFormclass = MyFormclass(
            generated_field=fake.postcode()
        )
        
    from dataclasses import asdict
    from pprint import pprint
    
    pprint(asdict(sample(ComposedClass())))
    
.. testoutput::

    {'field0': {'generated_field': 'Joseph'},
     'field1': {'generated_field': 'Sean'},
     'field_with_postcode': {'generated_field': '83827'}}


Class variables
^^^^^^^^^^^^^^^

If no type annotation is given
or the :py:class:`typing.ClassVar` annotation is used,
no field is generated
and a regular class variable is declared.

.. testsetup::

    import typing

.. testcode::

    @formclass
    class MyFormclass:
        class_var0 = "value0"
        class_var1: typing.ClassVar[str] = "value1"
        
    print(MyFormclass.class_var0)
    print(MyFormclass.class_var1)
        
.. testoutput::

    value0
    value1

.. testcode::

    MyFormclass(class_var0="foo")

.. testoutput::

    Traceback (most recent call last):
        ...
    TypeError: __init__() got an unexpected keyword argument 'class_var0'

Class variables are not sampled by the `~plato.formclasses.sample()` function.


Methods
^^^^^^^

Methods can be added to a `.formclass`.

.. testcode::

    @formclass
    class MyFormclass:
        name: str = "world"
        
        def greet(self):
            print(f"Hello, {self.name}!")

    MyFormclass().greet()
    sample(MyFormclass()).greet()

.. testoutput::

    Hello, world!
    Hello, world!


Properties
^^^^^^^^^^

Properties can be added to a `.formclass`.

.. testcode::

    @formclass
    class MyFormclass:
        name: str = "world"

        @property
        def greeting(self) -> str:
            return f"Hello, {self.name}!"

    print(MyFormclass().greeting)

.. testoutput::

    Hello, world!

Note that properties are considered fields,
in particular when converting the resulting :py:func:`~dataclasses.dataclass`
to other types.

.. testcode::

    from dataclasses import asdict, fields

    print(
        "Is greeting a field?",
        "greeting" in {f.name for f in fields(MyFormclass)}
    )
    print(
        "Is greeting part of dict conversion?",
        "greeting" in asdict(MyFormclass())
    )
    
.. testoutput::

    Is greeting a field? False
    Is greeting part of dict conversion? False


Derived fields
^^^^^^^^^^^^^^

It can be useful to derive the value of certain fields
from other fields.
This can be achieved
by declaring a method with the `.derivedfield` decorator.
Add the dependent fields as arguments to the method.

.. testcode::

    @formclass
    class User:
        first_name: str = fake.first_name()
        last_name: str = fake.last_name()

        @derivedfield
        def email(self, first_name, last_name) -> str:
            return f"{first_name}.{last_name}@example.net"

    from dataclasses import asdict
    from pprint import pprint
    
    pprint(asdict(sample(User())))
    
.. testoutput::

    {'email': 'Denise.Wright@example.net',
     'first_name': 'Denise',
     'last_name': 'Wright'}
     
A derived field can be overwritten
with a different value or provider
when needed.

.. testcode::

    pprint(asdict(sample(User(email="my-alias@mailz.org"))))

.. testoutput::

    {'email': 'my-alias@mailz.org', 'first_name': 'Melissa', 'last_name': 'Harris'}
    

Init-only variables
^^^^^^^^^^^^^^^^^^^

Sometimes you need values to derive specific field values,
but you do not want to store the original value as field in the formclass.
Use the `InitVar` type for this.
A field with this type can be provided as usual
when constructing the formclass;
you even must provide it
if it has no default value.
While,
it is not included in the fields of your formclass,
you can use it for your derived fields.
Just add an argument with the same name to yout `.derivedfield` method.

.. testcode::

    from datetime import date, timedelta
    from plato import InitVar

    @formclass
    class User:
        first_name: str = fake.first_name()
        last_name: str = fake.last_name()
        email_domain: InitVar[str] = "example.net"

        @derivedfield
        def email(self, email_domain) -> str:
            return f"{self.first_name}.{self.last_name}@{email_domain}"
            
    pprint(asdict(sample(User(email_domain="mailz.org"))))

.. testoutput::

    {'email': 'Denise.Wright@mailz.org',
     'first_name': 'Denise',
     'last_name': 'Wright'}
     
Note that `email_domain` is missing from the output.


Using formclasses
-----------------

When instantiating a `.formclass`,
you obtain a "template" for test data.
This allows to change
specific values or providers
as required by the respective test case.
To generate the actual test data,
call the `~plato.formclasses.sample()`
on such a "template".

.. testcode::

    fake = FromFaker()

    @formclass
    class User:
        first_name: str = fake.first_name()
        last_name: str = fake.last_name()
        bio: str = ""

        @derivedfield
        def email(self) -> str:
            return f"{self.first_name}.{self.last_name}@example.net"
            
    from dataclasses import asdict
    from pprint import pprint

    template = User(first_name="Plato", bio=fake.sentence())
    pprint(asdict(sample(template)))
    
.. testoutput::

    {'bio': 'Leg forget run book rise stage house.',
     'email': 'Plato.Wright@example.net',
     'first_name': 'Plato',
     'last_name': 'Wright'}
     
Sampling the same template multiple times will give different values;
making it easy to generate multiple test data instances.

.. testcode::

    pprint(asdict(sample(template)))
    pprint(asdict(sample(template)))
    
.. testoutput::

    {'bio': 'Station bag whole mission west amount son car.',
     'email': 'Plato.Harris@example.net',
     'first_name': 'Plato',
     'last_name': 'Harris'}
    {'bio': 'Though each energy catch pick ever strong bed.',
     'email': 'Plato.Hernandez@example.net',
     'first_name': 'Plato',
     'last_name': 'Hernandez'}
     

Seeding and reproducibility
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Test failures should be reproducible.
This also requires that the test data used can be reproduced.
Plato ensures this
by always using the same default random number generator seed.

If desired,
the seed can be set manually.
You might want to configure your test framework
to do this before every test
so that the set of executed tests does not affect the test data.

.. testcode::

    @formclass
    class MyFormclass:
        first_name: str = fake.first_name()
        
    plato.seed(42)
    print(sample(MyFormclass()).first_name)
    plato.seed(42)
    print(sample(MyFormclass()).first_name)
    
.. testoutput::

    Billy
    Billy

To make things even more reproducible,
Plato is designed in a way
that leaves generated values unaffected
if fields are added to or removed from a `.formclass`.

.. testcode::

    @formclass
    class MyFormclass:
        last_name: str = fake.last_name()

    plato.seed(42)
    print(sample(MyFormclass()).last_name)

    @formclass
    class MyFormclass:
        first_name: str = fake.first_name()
        last_name: str = fake.last_name()
        
    plato.seed(42)
    print(sample(MyFormclass()).last_name)

.. testoutput::

    Bullock
    Bullock

However,
generated values will change if the field name changes.

.. testcode::

    @formclass
    class MyFormclass:
        first_name: str = fake.last_name()

    plato.seed(42)
    print(sample(MyFormclass()).first_name)

    @formclass
    class MyFormclass:
        last_name: str = fake.last_name()

    plato.seed(42)
    print(sample(MyFormclass()).last_name)

.. testoutput::

    Williams
    Bullock


Providers
---------

While a `.formclass` defines the hierarchical structure of test data,
a `.Provider` defines how individual values are generated.

Currently,
Plato does not really have any providers of its own,
but provides the `.FromFaker` class to create providers
based on the `Faker <https://faker.readthedocs.io/en/latest/>`_ library.
Its delegates all method calls to Faker,
but returns a `.Provider` usuable with Plato,
instead of a value.

.. testcode::

    fake = FromFaker()
    print(fake.name())
    print(sample(fake.name()))
    
.. testoutput::

    <plato.providers.faker._FakerMethodProvider object at 0x...>
    Randy Garcia
    
The `.FromFaker` can be passed an existing :py:doc:`Faker <fakerclass>` instance.
This allows for example to make use of Faker's localization feature.

.. testcode::

    from faker import Faker

    fake = FromFaker(Faker(["en-US", "de-DE"]))

    print("English name:", sample(fake["en-US"].name()))
    print("German name:", sample(fake["de-DE"].name()))
    
.. testoutput::

    English name: Danielle Fletcher
    German name: Prof. Helmut Hentschel
    
.. testcleanup::

    fake = FromFaker()


Sharing values
^^^^^^^^^^^^^^

Sometimes it is desirable
to share the value generated with a provider
across multiple fields of a `.formclass`.
This can be done with the special `.Shared` provider decorator.

.. testcode:: shared

    @formclass
    class Address:
        street: str = fake.street_address()
        city: str = fake.city()
        postal_code: str = fake.postcode()

    @formclass
    class Order:
        billing_address: Address = Shared(Address())
        shipping_address: Address = billing_address

    from dataclasses import asdict
    from pprint import pprint

    pprint(asdict(sample(Order())))

.. testoutput:: shared

    {'billing_address': {'city': 'North Reginaburgh',
                         'postal_code': '03314',
                         'street': '310 Edwin Shore Suite 986'},
     'shipping_address': {'city': 'North Reginaburgh',
                          'postal_code': '03314',
                          'street': '310 Edwin Shore Suite 986'}}

This is in particular useful to include fields
of a child class
within the parent class.

.. testcode:: shared

    @formclass
    class Customer:
        mailing_address: Address = Shared(Address())
        postal_code: str = mailing_address.postal_code

    pprint(asdict(sample(Customer())))
    
Note that both *postal_codes* in the output are the same:
    
.. testoutput:: shared

    {'mailing_address': {'city': 'New Shane',
                         'postal_code': '20059',
                         'street': '81646 Rebecca Rapids Suite 486'},
     'postal_code': '20059'}


Implementing custom providers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom providers can be implemented
with the abstract `.Provider` base class.
It only requires
to provide an implementation
of the :py:meth:`.Provider.sample` method.
That method gets passed a `.Context`
which provides a `.Context.seed`
that should be used as random number generator seed
to ensure reproducability.
Alternatively,
a seeded :py:class:`~random.Random` instance is provided as `.Context.rng`.

.. testcode:: provider

    from plato.context import Context
    from plato.providers import Provider

    class RandomFloatProvider(Provider):
        def sample(self, context: Context) -> float:
            return context.rng.random()
            
    @formclass
    class MyFormclass:
        number: float = RandomFloatProvider()

    print(sample(MyFormclass()).number)

.. testoutput:: provider

    0.9355289927699928


Recipes and typical use cases
-----------------------------


Convert to JSON
^^^^^^^^^^^^^^^

To convert generated test data to JSON,
use :py:func:`~dataclasses.asdict` to convert the object into a dictionary first,
then use the :py:mod:`json` module to convert that dictionary to JSON.

.. testcode:: json

    from dataclasses import asdict
    import json

    @formclass
    class MyFormclass:
        string_value: str = fake.name()
        number_value: int = 42

    data = sample(MyFormclass())
    json = json.dumps(asdict(data))
    print(json)

.. testoutput:: json

    {"string_value": "Edwin Ford", "number_value": 42}


Use Plato as builder
^^^^^^^^^^^^^^^^^^^^

TODO


High-level states / variants
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO


Fill database with SQLAlchemy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO