import pytest
from decimal import Decimal

from base.accounts.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    AdminUserSerializer,
)
from base.accounts.models import Account, Plan, PlanType, ProfessionalRole
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def plan(db):
    return Plan.objects.create(
        type=PlanType.BASIC,
        name="Plano Básico",
        is_active=True,
    )


@pytest.fixture
def account(db, plan):
    return Account.objects.create(
        name="Empresa Teste",
        slug="empresa-teste",
        plan=plan,
    )


@pytest.fixture
def user(db, account):
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        account=account,
        first_name="João",
        last_name="Silva",
        role=ProfessionalRole.DIRETOR_EVENTO,
    )


@pytest.mark.django_db
class TestUserSerializer:
    def test_user_serializer_fields(self, user):
        serializer = UserSerializer(user)
        assert serializer.data["username"] == "testuser"
        assert serializer.data["email"] == "test@example.com"
        assert serializer.data["first_name"] == "João"
        assert serializer.data["full_name"] == "João Silva"
        assert serializer.data["can_access"] is True

    def test_user_serializer_read_only(self, user):
        serializer = UserSerializer(user)
        assert "id" in serializer.data
        assert "created_at" in serializer.data


@pytest.mark.django_db
class TestUserCreateSerializer:
    def test_create_serializer_valid(self, account):
        data = {
            "username": "novouser",
            "email": "novo@teste.com",
            "password": "senha1234",
            "password_confirm": "senha1234",
            "first_name": "Maria",
            "last_name": "Santos",
            "phone": "11988888888",
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_create_serializer_password_mismatch(self, account):
        data = {
            "username": "novouser",
            "email": "novo@teste.com",
            "password": "senha1234",
            "password_confirm": "senha_diferente",
            "first_name": "Maria",
            "last_name": "Santos",
        }
        serializer = UserCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "password_confirm" in serializer.errors

    def test_create_serializer_creates_user(self, account):
        data = {
            "username": "novouser",
            "email": "novo@teste.com",
            "password": "senha1234",
            "password_confirm": "senha1234",
            "first_name": "Maria",
            "last_name": "Santos",
            "phone": "11988888888",
        }
        serializer = UserCreateSerializer(data=data)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.username == "novouser"
        assert user.email == "novo@teste.com"


@pytest.mark.django_db
class TestUserUpdateSerializer:
    def test_update_serializer_fields(self, user):
        serializer = UserUpdateSerializer(user)
        assert "first_name" in serializer.fields
        assert "last_name" in serializer.fields
        assert "email" in serializer.fields
        assert "phone" in serializer.fields
        assert "photo" in serializer.fields

    def test_update_serializer_update(self, user):
        data = {
            "first_name": "João Atualizado",
            "phone": "11999999999",
        }
        serializer = UserUpdateSerializer(user, data=data)
        assert serializer.is_valid()
        serializer.save()
        user.refresh_from_db()
        assert user.first_name == "João Atualizado"
        assert user.phone == "11999999999"


@pytest.mark.django_db
class TestAdminUserSerializer:
    def test_admin_user_serializer_fields(self, user):
        serializer = AdminUserSerializer(user)
        assert serializer.data["username"] == "testuser"
        assert "blocked_reason" in serializer.fields
        assert "blocked_at" in serializer.fields

    def test_admin_user_update_password(self, user):
        data = {"password": "novasenha123"}
        serializer = AdminUserSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        user = serializer.save()
        assert user.check_password("novasenha123") is True
