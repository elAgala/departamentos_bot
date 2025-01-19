import os
import scrapy
import re

ARGENPROP_BASE_LINK = os.environ.get("ARGENPROP_BASE_LINK")
ARGENPROP_SEARCH_LINK = os.environ.get("ARGENPROP_SEARCH_LINK")


def price_to_number(price):
    return price.replace('.', '')


def parse_price(price):
    price_match = re.search(r'\d{1,3}(?:\.\d{3})*(?:,\d{2})?', price)

    if price_match:
        return price_to_number(price_match.group(0))
    else:
        return None


def parse_expenses(expenses):
    if expenses:
        expenses_text = expenses.strip()
        match = re.search(r'\d{1,3}(?:\.\d{3})*', expenses_text)
        return price_to_number(match.group(0)) if match else None
    else:
        return None


def extract_number(text):
    if text:
        match = re.search(r'(\d+)', text.strip())
        return match.group(0) if match else None
    return None


def get_nullable_field(field):
    if field:
        return field.strip()
    else:
        return None


def get_image(listing):
    first_image = (
        listing.css(".card__photos img::attr(src)").get()
        or listing.css(".card__photos img::attr(data-src)").get()
    )
    return first_image


def get_location(listing):
    locationText = listing.css(".card__title--primary::text").get()
    pattern = r"Departamento en Alquiler en (.+)"

    if locationText:
        match = re.search(pattern, locationText.strip())
        return match.group(1) if match else None
    else:
        return None


class ArgenpropSpider(scrapy.Spider):
    name = "argenprop"
    allowed_domains = ["argenprop.com"]
    if not ARGENPROP_BASE_LINK:
        raise EnvironmentError("BASE_LINK not specified")
    if not ARGENPROP_SEARCH_LINK:
        raise EnvironmentError("SEARCH_LINK not specified")

    start_urls = [
        ARGENPROP_BASE_LINK + ARGENPROP_SEARCH_LINK
    ]

    def parse(self, response):
        for listing in response.css(".listing__item"):
            yield {
                "link": ARGENPROP_BASE_LINK + listing.css('a.card::attr(href)').get(),
                "price": parse_price(listing.css('.card__price').get()),
                "expenses": parse_expenses(listing.css(".card__expenses::text").get()),
                "address": listing.css(".card__address::text").get().strip(),
                "rooms": extract_number(listing.css(".icono-cantidad_dormitorios + span::text").get()),
                "m2": extract_number(listing.css(".icono-superficie_cubierta + span::text").get()),
                "years": get_nullable_field(listing.css(".icono-antiguedad + span::text").get()),
                "image": get_image(listing),
                "location": get_location(listing)
            }

        # Follow pagination links
        # Update with the actual class
        next_page = response.css(".pagination__page-next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
