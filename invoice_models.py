"""Domain models for the commercial invoice generator.

Everything here is generic and uses fictitious sample data. It demonstrates
a "core + region" design: the same invoice structure is rendered differently
for each destination region (currency, bank block and trade-terms footer).
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Party:
    """A seller or buyer on the invoice."""
    name: str
    address: str
    city: str
    country: str
    tax_id: str = ""


@dataclass
class LineItem:
    description: str
    quantity: float
    unit_price: float

    @property
    def amount(self) -> float:
        return round(self.quantity * self.unit_price, 2)


@dataclass
class RegionConfig:
    """Per-region rules: currency, bank details and whether the invoice
    shows the FOB / freight / insurance trade-terms footer."""
    code: str
    currency: str
    currency_symbol: str
    bank_name: str
    bank_details: dict
    show_trade_terms: bool


# Fictitious banking data — for demonstration only.
REGIONS = {
    "AMERICA": RegionConfig(
        code="AMERICA",
        currency="USD",
        currency_symbol="$",
        bank_name="First Continental Bank",
        bank_details={
            "Account": "0012 3456 7890",
            "SWIFT": "FCBKUS33",
            "Routing": "021000021",
        },
        show_trade_terms=False,
    ),
    "EUROPE": RegionConfig(
        code="EUROPE",
        currency="EUR",
        currency_symbol="\u20ac",
        bank_name="Commerz Europa Bank",
        bank_details={
            "IBAN": "DE89 3704 0044 0532 0130 00",
            "BIC/SWIFT": "COBADEFFXXX",
        },
        show_trade_terms=True,
    ),
}


@dataclass
class Invoice:
    number: str
    issue_date: date
    seller: Party
    buyer: Party
    region: str  # key into REGIONS
    items: list = field(default_factory=list)
    incoterm: str = "FOB"
    freight: float = 0.0
    insurance: float = 0.0
    notes: str = ""

    @property
    def region_config(self) -> RegionConfig:
        try:
            return REGIONS[self.region]
        except KeyError:
            raise ValueError(f"Unknown region '{self.region}'. "
                             f"Valid regions: {', '.join(REGIONS)}")

    @property
    def subtotal(self) -> float:
        return round(sum(i.amount for i in self.items), 2)

    @property
    def total(self) -> float:
        extra = (self.freight + self.insurance) if self.region_config.show_trade_terms else 0.0
        return round(self.subtotal + extra, 2)

    def money(self, value: float) -> str:
        """Format a value with the region's currency symbol."""
        return f"{self.region_config.currency_symbol}{value:,.2f}"


def build_sample_invoice(region: str = "AMERICA", buyer_name: str = "", number: str = "") -> Invoice:
    """Return a ready-to-render sample invoice for the given region."""
    seller = Party(
        name="Acme Export Trading Co.",
        address="1200 Harbor Avenue, Unit 5",
        city="Santos",
        country="Brazil",
        tax_id="12.345.678/0001-90",
    )
    buyers = {
        "AMERICA": Party("Northwind Distributors Inc.", "450 Market Street",
                         "Chicago, IL", "United States", "US-98-7654321"),
        "EUROPE": Party("Rheinland Automotive GmbH", "Industriestrasse 14",
                        "Stuttgart", "Germany", "DE123456789"),
    }
    buyer = buyers.get(region, buyers["AMERICA"])
    if buyer_name:
        buyer.name = buyer_name

    items = [
        LineItem("Brake disc, ventilated (ref. BD-4410)", 120, 18.50),
        LineItem("Wheel bearing kit (ref. WB-2203)", 80, 32.75),
        LineItem("Timing belt set (ref. TB-9015)", 45, 54.90),
        LineItem("Oil filter, heavy duty (ref. OF-1180)", 300, 4.25),
    ]

    return Invoice(
        number=number or "INV-2026-0042",
        issue_date=date.today(),
        seller=seller,
        buyer=buyer,
        region=region,
        items=items,
        incoterm="FOB" if region == "AMERICA" else "CIF",
        freight=1850.00 if region == "EUROPE" else 0.0,
        insurance=420.00 if region == "EUROPE" else 0.0,
        notes="Goods of Brazilian origin. Payment within 30 days of B/L date.",
    )
