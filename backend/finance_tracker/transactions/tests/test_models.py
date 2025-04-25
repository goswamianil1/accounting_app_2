import pytest
from django.utils import timezone
from transactions.models import Transaction, Category
from factory import Faker
from factory.django import DjangoModelFactory

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = Faker('word')
    description = Faker('sentence')

class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    amount = Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    date = Faker('date_this_year')
    description = Faker('sentence')
    category = factory.SubFactory(CategoryFactory)

@pytest.mark.django_db
def test_transaction_creation():
    """Test that a transaction can be created with valid data"""
    transaction = TransactionFactory()
    assert transaction.pk is not None
    assert transaction.amount > 0
    assert transaction.date <= timezone.now().date()

@pytest.mark.django_db
def test_transaction_str():
    """Test the string representation of a transaction"""
    transaction = TransactionFactory(amount=100.50, description="Test Transaction")
    assert str(transaction) == "Test Transaction - $100.50"

@pytest.mark.django_db
def test_category_creation():
    """Test that a category can be created with valid data"""
    category = CategoryFactory()
    assert category.pk is not None
    assert len(category.name) > 0

@pytest.mark.django_db
def test_category_str():
    """Test the string representation of a category"""
    category = CategoryFactory(name="Test Category")
    assert str(category) == "Test Category" 