from dataclasses import asdict
from pprint import pprint

from plato import derivedfield, formclass, sample
from plato.providers.faker import FromFaker

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
    def fullname(self, first_name: str, last_name: str) -> str:
        return f"{first_name} {last_name}"

    @derivedfield
    def email(self, first_name: str, last_name: str) -> str:
        return f"{first_name}.{last_name}@example.com"


if __name__ == "__main__":
    pprint(asdict(sample(Customer())))
