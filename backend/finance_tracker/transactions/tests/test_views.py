import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from transactions.models import Transaction, Category
from .test_models import TransactionFactory, CategoryFactory

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def category():
    return CategoryFactory()

@pytest.fixture
def transaction(category):
    return TransactionFactory(category=category)

@pytest.mark.django_db
def test_list_transactions(client, transaction):
    """Test that transactions can be listed"""
    url = reverse('transaction-list')
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['amount'] == str(transaction.amount)

@pytest.mark.django_db
def test_create_transaction(client, category):
    """Test that a transaction can be created"""
    url = reverse('transaction-list')
    data = {
        'amount': '100.50',
        'date': '2023-01-01',
        'description': 'Test Transaction',
        'category': category.id
    }
    response = client.post(url, data)
    assert response.status_code == 201
    assert Transaction.objects.count() == 1

@pytest.mark.django_db
def test_update_transaction(client, transaction):
    """Test that a transaction can be updated"""
    url = reverse('transaction-detail', args=[transaction.id])
    data = {
        'amount': '200.75',
        'date': transaction.date.isoformat(),
        'description': 'Updated Transaction',
        'category': transaction.category.id
    }
    response = client.put(url, data)
    assert response.status_code == 200
    transaction.refresh_from_db()
    assert transaction.amount == 200.75

@pytest.mark.django_db
def test_delete_transaction(client, transaction):
    """Test that a transaction can be deleted"""
    url = reverse('transaction-detail', args=[transaction.id])
    response = client.delete(url)
    assert response.status_code == 204
    assert Transaction.objects.count() == 0

@pytest.mark.django_db
def test_list_categories(client, category):
    """Test that categories can be listed"""
    url = reverse('category-list')
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['name'] == category.name 