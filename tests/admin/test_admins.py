import pytest
from unittest.mock import MagicMock

from base.accounts.admin import UserAdmin, AccountAdmin, PlanAdmin
from base.clients.admin import ClientAdmin
from base.jobs.admin import JobAdmin
from base.expenses.admin import ExpenseAdmin
from base.services.admin import ServiceAdmin


@pytest.mark.django_db
class TestAccountAdmin:
    def test_account_admin_list_display(self):
        admin = AccountAdmin(MagicMock(), MagicMock())
        assert "name" in admin.list_display
        assert "slug" in admin.list_display
        assert "account_type" in admin.list_display

    def test_account_admin_list_filter(self):
        admin = AccountAdmin(MagicMock(), MagicMock())
        assert "account_type" in admin.list_filter
        assert "is_active" in admin.list_filter


@pytest.mark.django_db
class TestUserAdmin:
    def test_user_admin_list_display(self):
        admin = UserAdmin(MagicMock(), MagicMock())
        assert "username" in admin.list_display
        assert "email" in admin.list_display
        assert "account" in admin.list_display
        assert "role" in admin.list_display

    def test_user_admin_list_filter(self):
        admin = UserAdmin(MagicMock(), MagicMock())
        assert "is_active" in admin.list_filter
        assert "is_blocked" in admin.list_filter
        assert "account" in admin.list_filter
        assert "role" in admin.list_filter

    def test_user_admin_search_fields(self):
        admin = UserAdmin(MagicMock(), MagicMock())
        assert "username" in admin.search_fields
        assert "email" in admin.search_fields


@pytest.mark.django_db
class TestClientAdmin:
    def test_client_admin_list_display(self):
        admin = ClientAdmin(MagicMock(), MagicMock())
        assert "name" in admin.list_display
        assert "email" in admin.list_display
        assert "phone" in admin.list_display


@pytest.mark.django_db
class TestJobAdmin:
    def test_job_admin_list_display(self):
        admin = JobAdmin(MagicMock(), MagicMock())
        assert "title" in admin.list_display
        assert "client" in admin.list_display
        assert "start_date" in admin.list_display
        assert "status" in admin.list_display

    def test_job_admin_list_filter(self):
        admin = JobAdmin(MagicMock(), MagicMock())
        assert "status" in admin.list_filter
        assert "payment_status" in admin.list_filter
        assert "event_type" in admin.list_filter


@pytest.mark.django_db
class TestExpenseAdmin:
    def test_expense_admin_list_display(self):
        admin = ExpenseAdmin(MagicMock(), MagicMock())
        assert "category" in admin.list_display
        assert "value" in admin.list_display
        assert "date" in admin.list_display


@pytest.mark.django_db
class TestServiceAdmin:
    def test_service_admin_list_display(self):
        admin = ServiceAdmin(MagicMock(), MagicMock())
        assert "name" in admin.list_display
        assert "hourly_rate" in admin.list_display
        assert "is_active" in admin.list_display
