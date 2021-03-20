Getting Started
===============

Installation
------------

Run the following in your command line::

    pip install -U plato
    

Generate your first test data
-----------------------------

In this example we generate data for a customer
with a name, email, and billing address.

First,
we import the *formclass* and *formProperty* decorators,
as well as the *sample* function.
These are the most important objects in Plato
and you will import them most of the time
when working with Plato.
We also import *FromFaker*
which allows us to generate some realistic sounding values
with the excellent `Faker library <https://faker.readthedocs.io/en/master/>`_.
Because we need an actual instance of *FromFaker*,
we also create that.

.. testcode::

    from plato import formclass, formProperty, sample
    from plato.providers.faker import FromFaker
    
    fake = FromFaker()

Next, we define our first *formclass*
to generate addresses.

.. testcode::

    @formclass  # (1)
    class Address:
        street: str = fake.street_address()  # (2)
        postal_code: str = fake.postcode()
        city: str = fake.city()
        country: str = "USA"  # (3)
        
Note the similarities to Python's :py:mod:`dataclasses`.
    
1. We add the *formclass* decorator to mark the class as a formclass.
2. We define a number of fields with a type annotation.
   We use the *fake* object to declare that the data should be generated
   following specific Faker patterns.
3. We can also just assign a constant value as default.
    
.. testcode::

    @formclass
    class Customer:
        first_name: str = fake.first_name()
        last_name: str = fake.last_name()
        billing_address: Address = Address()  # (4)
    
        @property  # (5)
        def fullname(self) -> str:
            return f"{self.first_name} {self.last_name}"
    
        @formProperty  # (6)
        def email(self) -> str:
            return f"{self.first_name}.{self.last_name}@example.com"
            
4. We can use the ``Address`` *formclass*
   to build up hierarchically structured data.
   The *billing_address* will be filled with a generated address.
5. Standard Python properties can be used to add attributes for derived data.
6. Plato also adds a special kind of property, the *formProperty*.
   It is similar
   but allows to be assigned a different value
   when the data is generated.
   
By using the *sample* method
on a *formclass* instance,
a Python :py:func:`~dataclasses.dataclass` instance
containing the desired test data is generated.
We can use standard *dataclass* functions,
for example *asdict* to convert it into a dictionary
(or some other desired format),
and than print it nicely with *pprint*.

.. testcode::

    from dataclasses import asdict
    from pprint import pprint

    pprint(asdict(sample(Customer())))

.. testoutput::

    {'billing_address': {'city': 'North Reginaburgh',
                         'country': 'USA',
                         'postal_code': '03314',
                         'street': '310 Edwin Shore Suite 986'},
     'email': 'Denise.Wright@example.com',
     'first_name': 'Denise',
     'last_name': 'Wright'} 
     
If you sample the same *formclass* multiple times,
you will get different values each time.
This allows to generate larger datasets easily.
However,
when running the same Python script multiple times,
Plato will generate the same values each time
to make tests reproducible.

Next steps
----------

* :doc:`user-guide`
* :doc:`api/modules`
