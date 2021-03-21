User Guide
==========

.. testsetup::

    from plato import formclass, sample

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
that exposes the API of the `Faker <https://faker.readthedocs.io/en/master/>`_
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

    <plato.providers.faker.FakerMethodProvider object at 0x...>
    
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
or the :py:class`typing.ClassVar` annotation is used,
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


Sharing values
^^^^^^^^^^^^^^

Using formclasses
-----------------

sample

Seeding and reproducibility
---------------------------

setting seed
removing/adding fields

Providers
---------

TODO


Implementing custom providers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO


Recipes and typical use cases
-----------------------------

TODO


Convert to JSON
^^^^^^^^^^^^^^^

TODO


Use Plato as builder
^^^^^^^^^^^^^^^^^^^^

TODO


Fill database with SQLAlchemy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO