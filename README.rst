.. image:: logo/logo.svg
  :alt: Plato logo
  :width: 150px
  :align: center

.. image:: https://github.com/py-plato/plato/actions/workflows/workflow.yml/badge.svg?branch=main
  :target: https://github.com/py-plato/plato/actions/workflows/workflow.yml
  :alt: Build and release pipeline
  

.. image:: https://codecov.io/gh/py-plato/plato/branch/main/graph/badge.svg?token=UEVIAHO33E
  :target: https://codecov.io/gh/py-plato/plato
  :alt: Code coverage  

.. image:: https://img.shields.io/pypi/v/plato
  :target: https://pypi.org/project/plato
  :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/pyversions/plato
  :target: https://pypi.org/project/plato
  :alt: Python versions
  
.. image:: https://img.shields.io/pypi/l/plato
  :target: https://github.com/py-plato/plato/blob/main/LICENSE
  :alt: PyPI - License

Plato
=====

Plato makes it easy
to generate complex,
but consistent and realistic data
for tests
with a declarative syntax
inspired by dataclasses.

.. code-block:: python

    fake = FromFaker()


    @formclass
    class Address:
        street: str = fake.street_address()
        postal_code: str = fake.postcode()
        city: str = fake.city()
        country: str = "USA"


    @formclass
    class Customer:
        first_name: str = fake.first_name()
        last_name: str = fake.last_name()
        billing_address: Address = Address()

        @property
        def fullname(self) -> str:
            return f"{self.first_name} {self.last_name}"

        @derivedfield
        def email(self) -> str:
            return f"{self.first_name}.{self.last_name}@example.com"
            

    pprint(asdict(sample(Customer())))
    # Prints:
    # {'billing_address': {'city': 'North Reginaburgh',
    #                  'country': 'USA',
    #                  'postal_code': '03314',
    #                  'street': '310 Edwin Shore Suite 986'},
    #  'email': 'Denise.Wright@example.com',
    #  'first_name': 'Denise',
    #  'last_name': 'Wright'}
    

Vision and Guiding Priniciples
------------------------------

* Generating consistent and realistic test data should be **easy**. The more
  effort it is to produce releastic or consistent test data, the more likely
  developers take short cuts. This tends to couple tests to the implementation
  (e.g., because only the fields required for a specific implementation are set,
  or certain fields are inconsistent with the values of other fields). It also
  makes it harder to understand, based on the tests, what the expected
  production data will look like, or can be outright confusing.
* The code should be **declarative**. When creating test data one should not be
  concerned with *how* it is created, but with *what* the structure of that
  data.
* Try **minimize boilerplate** to reduce the effort of producing consistent and
  realistic test data (see above).
* To be able to easily create complex and varied test data, things should be
  **composable**.
* Test results should be **reproducible**. Thus, all test data will be generated
  based on a fixed (but changeable) seed. Plato even tries to keep produced
  values reproducible when fields are added or deleted from a class.
* One should have **flexibility** in how the generated data is used. Therefore,
  Plato produces dataclasses as output, that can be easily converted into
  dictionaries and other sorts of objects.
* **No collisions** of field names in the test data with Plato's API. This is
  achieved similar to dataclasses by not defining Plato's API as member methods
  on the formclasses, but as separate functions processing a formclass.


Project Status and Roadmap
--------------------------

The project is currently in a very early stage where I still explore the design
space of the API. Thus, breaking changes have to be expected at any time.

The current focus is on finishing the core API together with documentation and
examples to test out whether the API would work in real world scenarios.

To get something useful working quickly, Plato currently relies heavily on
`Faker <https://faker.readthedocs.io/en/master/>`_. In the future, it is intended
that Plato also offers certain Providers, but implementing these is not yet the
focus.

Here is a very roughly sorted list of additional features and to-dos to consider:

* Setup CI, static typechecking, linting, auto-formatting
* Setup website
* Design a logo
* Constructor parameters that do not appear as field in the dataclass.
* Express relations between objects (apart from the composition already
  possible), especially with respect to relational databases.
* A standard set of providers
* Documentation
* Examples

  * Usage with pytest
  * Usage as builder
  * Usage with ORM

* A command line interface to generate data (i.e. in JSON format that than can
  be used for web requests with some other tool)
* ORM integration

  * With possibility of cleaning up generated data

* pytest integration


Alternatives
------------

* `Faker <https://faker.readthedocs.io/en/master/>`_ is excellent for generating
  individual pieces of information such as a realistic name, a bank account
  number, a street address etc. However, it does not provide a convenient way
  to generate more complex objects.
* `Factory Boy <https://factoryboy.readthedocs.io/en/stable/>`_ has a very
  similar aim and scope. As it has been around longer and it is stable, opposed
  to Plato, you should prefer it for testing production code. However, Plato
  will have some advantages, such as:

  * Syntax with less boilerplate.
  * It is easier to compose from fields of other sampled objects.
  * API that avoids name collisions, whereas in Factory Boy one has to work
    around it with renames.
  * By producing data classes conversion into other data formats such as dicts,
    JSON, etc. is easy and does not require to declare a model class duplicating
    a lot of information.
  * Reproducible test data even when deleting or adding fields on an object.

Inspirations
------------

Plato was inspired by:

* Company-internal talks at
  `TNG Technology Consulting GmbH <https://www.tngtech.com/>`_ (my employer).
* `Strawberry <https://github.com/strawberry-graphql/strawberry>`_ which gave
  me the idea to apply the dataclasses approach to other problems.
* `Nengo <https://www.nengo.ai/>`_ which gave me the idea to seed random number
  generator in a way robust against field removal and additions.
* `Factory Boy <https://factoryboy.readthedocs.io/en/stable/>`_

Contributing
------------

Contributions are welcome in general.

For bugs, feel free to open issues or pull requests.

If you have an ideas, feedback, or feature requests, also open an issue.

Given the early stage of the project, if you want to implement a feature,
I suggest that you open an issue first to discuss the details and ensure that
it aligns with the general direction the project is moving into.

Note that it might take me a bit to react as I am working on Plato in my free
time besides other projects.

The name
--------

The ancient greek philosopher Plato is well known for his *theory of
forms*. It proposes that, the objects existing in reality are imitations of more
pure “Ideas” or “Forms” which are the non-physical essence of things.

In analogy, the library Plato allows you to define the essence or “Form“ of your
test data from which the concrete objects used in the tests are derived.