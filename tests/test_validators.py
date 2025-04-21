from parser_service.validators import (
    validate_name,
    validate_upc,
    validate_price_tax,
    validate_availability,
    validate_url,
    record_is_duplicate,
)

def test_validate_name():
    assert not validate_name("")      # empty
    assert not validate_name("A" * 300)  # too long
    assert validate_name("Normal Title")

def test_validate_upc():
    assert not validate_upc("")
    assert not validate_upc("123")
    assert not validate_upc("INVALID!@#%^")
    assert validate_upc("A1B2C3D4E5F6G7H8")  # exactly 16 alnum

def test_validate_price_tax():
    assert not validate_price_tax(-1.0, "Price")
    assert validate_price_tax(0.0, "Price")
    assert validate_price_tax(12.34, "Tax")

def test_validate_availability():
    assert not validate_availability(-5)
    assert validate_availability(0)
    assert validate_availability(10)


def test_validate_url():
    assert validate_url("https://geras.com/a", base="https://geras.com/")
    assert not validate_url("https://blogas.com/a", base="https://geras.com/")

def test_record_is_duplicate():
    good = {
        "Name": "Book",
        "UPC": "1234567890ABCDEF",
        "Price_excl_tax": 10.0,
        "Tax": 2.0,
        "Availability": 3,
        "URL": "https://books.toscrape.com/foo"
    }
    seen = set()
    assert not record_is_duplicate(good["UPC"], seen)
    # duplicate
    seen.add(good["UPC"])
    assert record_is_duplicate(good["UPC"], seen)

