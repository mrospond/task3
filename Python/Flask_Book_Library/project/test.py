import pytest

from project import db, app
from project.customers.models import Customer


@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.mark.parametrize(
    "name,city,age,pesel,street,appNo",
    [
        ("Michal", "Warszawa", 30, "12345678901", "Plac Politechniki", "cokolwiek"),
        ("Andrzej", "Lodz", 23, "10987654321", "Titanic", "cokolwiek1"),
        ("Kacper", "Poznan", 64, "11111111111", "Dluga", "cokolwiek2"),
    ],
)
def test_customer_creation_with_valid_data(test_client, name, city, age, pesel, street, appNo):
    with app.app_context():
        customer = Customer(name, city, age, pesel, street, appNo)

        db.session.add(customer)
        db.session.commit()

        item=Customer.query.filter_by(name=name).first()
        assert item is not None
        assert item.name == name
        assert item == customer


def test_customer_creation_with_negative_age(test_client):
    with app.app_context():
        with pytest.raises(Exception):
            customer = Customer(name=name, city=city, age=-15, pesel=pesel, street=street, appNo=appNo)
            db.session.add(customer)
            db.session.commit()


@pytest.mark.parametrize(
    "name,city,age,pesel,street,appNo",
    [
        (None, "Warszawa", 26, 1234,"Random Street", 123123),
        ("Tomasz", "Warszawa", None, 1234,123, 123123),
        (None, None, 26, 1234,"Random Street", 123123),
        ("Tomasz2", "Warszawa", 26, 1234,"Random Street", "\n\nlalala\t\t\tlal\nala"),
        ("Tomasz3", 1234, "26", 1234,"Random Street", 123123),
        ("Tomasz4", "Warszawa", -26, 1234,123, "123123"*100),
        ("Tomasz5"*1000, "None", None, None, None, None),
    ]
)
def test_customer_creation_invalid_data(test_client, name, city, age, pesel, street, appNo):
    with app.app_context():
        with pytest.raises(Exception):
            customer = Customer(name=name, city=city, age=age, pesel=pesel, street=street,appNo=appNo)
            db.session.add(customer)
            db.session.commit()

def test_duplicate_customer_name_creation(test_client):
    with app.app_context():
        name = "Pan Tadeusz"
        customer = Customer(name=name, city="Warszawa", age=123, pesel="12312", street="nie plac pol", appNo="123")
        customer2 = Customer(name=name, city="Warszawa", age=123, pesel="pesel", street="plac pol", appNo="123")

        db.session.add(customer)
        db.session.commit()

        with pytest.raises(Exception):
            db.session.add(customer2)
            db.session.commit()

@pytest.mark.parametrize(
    "sql_injection",
    [
        "-- or #",
        "\" OR 1 = 1 -- -",
        "'''''''''''UNION SELECT '2",
        "1' ORDER BY 1--+",
        "' UNION SELECT(columnname ) from tablename --",
        ",(select * from (select(sleep(10)))a)",
        "Test'; DROP TABLE customers;--",
    ],
)
def test_sql_injection(test_client, sql_injection):
    with app.app_context():
        with pytest.raises(Exception):
            customer = Customer(name=sql_injection, city="Warszawa", age=123, pesel="12312", street="plac pol", appNo="123")
            db.session.add(customer)
            db.session.commit()

@pytest.mark.parametrize(
    "xss",
    [
        "\"-prompt(8)-\"",
        "'-prompt(8)-'",
        "<img/src/onerror=prompt(8)>",
        "<script\\x20type=\"text/javascript\">javascript:alert(1);</script>",
        "<script src=1 href=1 onerror=\"javascript:alert(1)\"</script>",
        "<script>alert('XSS');</script>",
    ],
)
def test_xss(test_client, xss):
    with app.app_context():
        with pytest.raises(Exception):
            customer = Customer(name=xss, city="Warszawa", age=123, pesel="12312", street="nie plac pol", appNo="123")
            db.session.add(customer)
            db.session.commit()

@pytest.mark.parametrize(
    "name,city,age,pesel,street,appNo",
    [
        ("Tomasz1", "Warszawa"*10, 26, "1234", "123"*10, "123123"*10),
        ("Tomasz1"*10, "Warszawa"*10, 26, "1234"*10, "123"*10, "123123"*10),
        ("Tomasz1"*100, "Warszawa"*100, 26, "1234"*100, "123"*100, "123123"*100),
        ("Tomasz1"*1000, "Warszawa"*1000, 26, "1234"*1000, "123"*1000, "123123"*1000),
    ],
)
def test_extreme(test_client, name, city, age, pesel, street, appNo):
    with app.app_context():
        with pytest.raises(Exception):
            customer = Customer(name=name, city=city, age=age, pesel=pesel, street=street, appNo=appNo)
            db.session.add(customer)
            db.session.commit()
