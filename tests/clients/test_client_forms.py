import pytest

from base.clients.forms import ClientForm


@pytest.mark.django_db
class TestClientForm:
    def test_client_form_fields(self):
        form = ClientForm()
        assert "name" in form.fields
        assert "email" in form.fields
        assert "phone" in form.fields
        assert "document" in form.fields
        assert "address" in form.fields
        assert "notes" in form.fields

    def test_client_form_phone_required(self):
        form = ClientForm()
        assert form.fields["phone"].required is True

    def test_client_form_email_required(self):
        form = ClientForm()
        assert form.fields["email"].required is True
