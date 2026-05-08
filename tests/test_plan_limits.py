import json
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from base.accounts.models import Plan, PlanType, PersonalTask, PersonalAgendaEvent
from base.clients.models import Client
from base.jobs.models import Job
from base.expenses.models import Expense, ExpenseCategory
from base.quote.models import Quote


class PlanLimitsTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            type=PlanType.FREE,
            name="Basic Test",
            max_clients=1,
            max_jobs=1,
            max_quotes=1,
            max_expenses=1,
            max_personal_tasks=1,
            max_personal_agenda_events=1,
            max_agenda_events=1,
            is_active=True,
        )
        User = get_user_model()
        self.user = User.objects.create_user(
            username="plan_user",
            password="123456",
            email="plan@test.com",
            plan=self.plan,
        )
        self.client.force_login(self.user)

        self.client_obj = Client.objects.create(
            created_by=self.user,
            name="Cliente A",
            phone="11999999999",
        )
        self.job = Job.objects.create(
            created_by=self.user,
            client=self.client_obj,
            title="Job A",
            start_date=date.today(),
        )
        self.quote = Quote.objects.create(
            created_by=self.user,
            client=self.client_obj,
            title="Quote A",
            hourly_rate=100,
            work_hours=1,
        )
        self.expense = Expense.objects.create(
            performed_by=self.user,
            job=self.job,
            category=ExpenseCategory.OTHER,
            value=10,
            date=date.today(),
        )
        self.task = PersonalTask.objects.create(
            user=self.user,
            title="Task A",
            date=date.today(),
        )
        self.agenda = PersonalAgendaEvent.objects.create(
            user=self.user,
            title="Agenda A",
            date=date.today(),
            start_time="10:00",
            end_time="11:00",
        )

    def assert_redirect_to_plans(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn("/app/planos/", response.url)

    def test_blocks_job_creation_when_limit_reached(self):
        response = self.client.get(reverse("jobs:create"))
        self.assert_redirect_to_plans(response)

    def test_blocks_quote_creation_when_limit_reached(self):
        response = self.client.get(reverse("quote:create"))
        self.assert_redirect_to_plans(response)

    def test_blocks_expense_creation_when_limit_reached(self):
        response = self.client.get(reverse("expenses:create"))
        self.assert_redirect_to_plans(response)

    def test_blocks_client_quick_create_when_limit_reached(self):
        response = self.client.post(
            reverse("clients:quick_create"),
            {"name": "Novo", "phone": "11988887777", "email": "x@x.com"},
        )
        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload.get("code"), "PLAN_LIMIT_REACHED")

    def test_blocks_personal_task_create_when_limit_reached(self):
        response = self.client.post(
            reverse("accounts:personal_tasks"),
            data=json.dumps(
                {
                    "action": "create",
                    "title": "Task B",
                    "date": str(date.today()),
                    "time": "10:00",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload.get("code"), "PLAN_LIMIT_REACHED")

    def test_blocks_personal_agenda_create_when_limit_reached(self):
        response = self.client.post(
            reverse("accounts:personal_agenda"),
            data=json.dumps(
                {
                    "action": "create",
                    "title": "Agenda B",
                    "date": str(date.today()),
                    "time": "10:00",
                    "duration": "1h",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        payload = response.json()
        self.assertEqual(payload.get("code"), "PLAN_LIMIT_REACHED")

    def test_zero_limit_means_unlimited(self):
        self.plan.max_personal_tasks = 0
        self.plan.save(update_fields=["max_personal_tasks"])

        response = self.client.post(
            reverse("accounts:personal_tasks"),
            data=json.dumps(
                {
                    "action": "create",
                    "title": "Task Unlimited",
                    "date": str(date.today()),
                    "time": "12:00",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("success"))
