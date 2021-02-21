from dataclasses import dataclass, asdict
from decimal import Decimal
from plato.shapeclasses import staticProperty
from pprint import pprint

from faker import Faker

from plato import Provider, sample, shapeclass, Shared
from plato.providers.faker import FromFaker
from plato.shapeclasses import staticProperty

fake = FromFaker(Faker(["en-CA", "de-DE"]))

# TODO generate either address randomly => abstract flag, might produce derived class flag
@shapeclass
class Address:
    street: str
    city: str
    zip_code: str
    country: str
    name: str = "uiae"  # FIXME providers in base classes do not run


@shapeclass
class GermanPostalCodeWithCity:
    zip_code: str = fake["de-DE"].postcode()
    city: str = fake["de-DE"].city()


@shapeclass
class GermanAddress:
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


@shapeclass
class CanadianAddress:
    street: str = fake["en-CA"].street_address()

    zip_code_and_city = Shared(CanadianPostalCodeWithCityProvider())
    city: str = zip_code_and_city.city
    zip_code: str = zip_code_and_city.zip_code

    country: str = "Canada"


@shapeclass
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


@shapeclass
class Price:
    locale: str
    # locale: Hidden[str]
    base_price: Decimal = fake.pydecimal(1, 2)

    @staticProperty
    def vat_percent(self) -> Decimal:
        return SelectProvider(
            self.locale,
            {
                "en-CA": fake.random_element([Decimal(5), Decimal(13)]),
                "de-DE": fake.random_element([Decimal(7), Decimal(19)]),
            },
        )


@shapeclass
class OrderLine:
    locale: str
    quantity: int = fake.pyint(1, 10)
    product: Product = Product()
    price: Price = None

    def __post_init__(self):
        self.price = Price(self.locale)


class OrderNumber(Provider):
    numbers_issued = 0

    def sample(self, context):
        order_no = f"ABC-{self.numbers_issued:05d}"
        self.numbers_issued += 1
        return order_no

    def __deepcopy__(self, memo):
        return self


class ListProvider(Provider):
    def __init__(self, min_elements: int, max_elements: int, provider: Provider):
        self.min_elements = min_elements
        self.max_elements = max_elements
        self.provider = provider

    def sample(self, context):
        num_elements = context.rng.randint(self.min_elements, self.max_elements + 1)
        return [sample(self.provider, context) for _ in range(num_elements)]


# want different addresses by default, but allow for matching
@shapeclass
class Order:
    locale: str = fake.random_element(["en-CA", "de-DE"])

    order_number: str = OrderNumber()  # globally unique

    @staticProperty
    def billing_address(self) -> Address:
        return {
            "de-DE": GermanAddress(),
            "en-CA": CanadianAddress(),
        }[self.locale]

    @staticProperty
    def shipping_address(self) -> Address:
        return self.billing_address

    @staticProperty
    def order_lines(self) -> str:
        return ListProvider(1, 5, OrderLine(self.locale))


if __name__ == "__main__":
    pprint(asdict(sample(Order())), width=180)
    pprint(asdict(sample(Order())), width=180)
    pprint(asdict(sample(Order())), width=180)
    pprint(asdict(sample(Order())), width=180)