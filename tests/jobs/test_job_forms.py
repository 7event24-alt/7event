import pytest
from django import forms

from base.jobs.forms import JobForm
from base.jobs.models import EventType, JobStatus, PaymentType, PaymentStatusJob


@pytest.mark.django_db
class TestJobForm:
    def test_job_form_fields(self):
        form = JobForm()
        assert "client" in form.fields
        assert "title" in form.fields
        assert "event_type" in form.fields
        assert "start_date" in form.fields
        assert "end_date" in form.fields
        assert "location" in form.fields
        assert "description" in form.fields
        assert "cache" in form.fields
        assert "status" in form.fields

    def test_job_form_event_type_choices(self):
        form = JobForm()
        event_type_choices = form.fields["event_type"].choices
        assert len(event_type_choices) == 15
        assert EventType.CORPORATIVO in [c[0] for c in event_type_choices]
        assert EventType.LIVES in [c[0] for c in event_type_choices]

    def test_job_form_status_choices(self):
        form = JobForm()
        status_choices = form.fields["status"].choices
        assert JobStatus.PENDING in [c[0] for c in status_choices]
        assert JobStatus.CONFIRMED in [c[0] for c in status_choices]
        assert JobStatus.COMPLETED in [c[0] for c in status_choices]
        assert JobStatus.CANCELLED in [c[0] for c in status_choices]

    def test_job_form_payment_type_choices(self):
        form = JobForm()
        payment_choices = form.fields["payment_type"].choices
        assert ("", "Selecione o tipo de pagamento...") in payment_choices
        assert PaymentType.FULL in [c[0] for c in payment_choices]

    def test_job_form_widget_types(self):
        form = JobForm()
        assert isinstance(form.fields["start_date"].widget, forms.TextInput)
        assert isinstance(form.fields["event_type"].widget, forms.Select)
        assert isinstance(form.fields["cache"].widget, forms.NumberInput)

    def test_job_form_end_date_not_required(self):
        form = JobForm()
        assert form.fields["end_date"].required is False
