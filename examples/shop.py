from dataclasses import InitVar, asdict, dataclass
from decimal import Decimal
from pprint import pprint

from faker import Faker

from plato import Provider, Shared, formclass, sample
from plato.formclasses import derivedfield
from plato.providers.faker import FromFaker

fake = FromFaker(Faker(["en-CA", "de-DE"]))

# TODO generate either address randomly => abstract flag, might produce derived class flag
@formclass
class Address:
    street: str
    city: str
    zip_code: str
    country: str
    name: str = fake.name()


@formclass
class GermanPostalCodeWithCity:
    zip_code: str = fake["de-DE"].postcode()
    city: str = fake["de-DE"].city()


@formclass
class GermanAddress(Address):
    street: str = fake["de-DE"].street_address()

    zip_code_and_city = Shared(GermanPostalCodeWithCity())
    city: str = zip_code_and_city.city
    zip_code: str = zip_code_and_city.zip_code

    country: str = "Germany"


@dataclass
class CanadianPostalCodeWithCity:
    zip_code: str
    city: str


class CanadianPostalCodeWithCityProvider(Provider):
    def sample(self, context):
        return context.rng.choice(
            (
                CanadianPostalCodeWithCity("N2L 3G1", "Waterloo"),
                CanadianPostalCodeWithCity("N2J 1A3", "Waterloo"),
                CanadianPostalCodeWithCity("V5K 0A4", "Vancouver"),
            )
        )


@formclass
class CanadianAddress(Address):
    street: str = fake["en-CA"].street_address()

    zip_code_and_city = Shared(CanadianPostalCodeWithCityProvider())
    city: str = zip_code_and_city.city
    zip_code: str = zip_code_and_city.zip_code

    country: str = "Canada"


@formclass
class Product:
    name: str = fake.random_element(["Apple", "Banana", "Orange", "Pear"])
    product_number: str = fake.bothify("?????-###")
    description: str = fake.paragraph()


class SelectProvider(Provider):
    def __init__(self, provider, dispatch_table):
        self.dispatch_table = dispatch_table
        self.provider = provider

    def sample(self, context):
        value = self.provider
        if isinstance(value, Provider):
            value = value.sample(context)
        return self.dispatch_table[value].sample(context)


@formclass
class Price:
    locale: InitVar[str]
    base_price: Decimal = fake.pydecimal(1, 2)

    @derivedfield
    def vat_percent(self, locale) -> Decimal:
        return SelectProvider(
            locale,
            {
                "en-CA": fake.random_element([Decimal(5), Decimal(13)]),
                "de-DE": fake.random_element([Decimal(7), Decimal(19)]),
            },
        )


@formclass
class OrderLine:
    locale: str
    quantity: int = fake.pyint(1, 10)
    product: Product = Product()

    @derivedfield
    def price(self, locale) -> Price:
        return Price(locale)


class OrderNumber(Provider):
    numbers_issued = 0

    def sample(self, context):
        order_no = f"ABC-{self.numbers_issued:05d}"
        self.numbers_issued += 1
        return order_no


class ListProvider(Provider):
    def __init__(self, min_elements: int, max_elements: int, provider: Provider):
        self.min_elements = min_elements
        self.max_elements = max_elements
        self.provider = provider

    def sample(self, context):
        num_elements = context.rng.randint(self.min_elements, self.max_elements + 1)
        return [sample(self.provider, context) for _ in range(num_elements)]


# want different addresses by default, but allow for matching
@formclass
class Order:
    locale: str = fake.random_element(["en-CA", "de-DE"])

    order_number: str = OrderNumber()  # globally unique

    @derivedfield
    def billing_address(self, locale) -> Address:
        return {
            "de-DE": GermanAddress(),
            "en-CA": CanadianAddress(),
        }[locale]

    @derivedfield
    def shipping_address(self, billing_address) -> Address:
        return billing_address

    @derivedfield
    def order_lines(self, locale) -> str:
        return ListProvider(1, 5, OrderLine(locale))


if __name__ == "__main__":
    pprint(asdict(sample(Order())), width=180)
    pprint(asdict(sample(Order())), width=180)
    pprint(asdict(sample(Order())), width=180)
    pprint(asdict(sample(Order())), width=180)
