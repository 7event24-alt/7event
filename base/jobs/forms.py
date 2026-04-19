from django import forms
from django.contrib.auth import get_user_model
from .models import Job, EventType, JobStatus, PaymentType, PaymentStatusJob

User = get_user_model()


class JobForm(forms.ModelForm):
    event_type = forms.ChoiceField(
        choices=[("", "Selecione o tipo de serviço...")] + list(EventType.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
            }
        ),
        required=False,
        label="Tipo de Serviço",
    )
    start_date = forms.DateField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                "type": "date",
            }
        ),
        required=True,
        label="Data do Evento",
    )
    end_date = forms.DateField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                "type": "date",
            }
        ),
        required=False,
    )
    payment_date = forms.DateField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                "type": "date",
            }
        ),
        required=False,
    )
    payment_partial_date = forms.DateField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                "type": "date",
            }
        ),
        required=False,
    )
    payment_remaining_date = forms.DateField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                "type": "date",
            }
        ),
        required=False,
    )
    payment_type = forms.ChoiceField(
        choices=[("", "Selecione o tipo de pagamento...")] + list(PaymentType.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
            }
        ),
        required=False,
        label="Tipo de Pagamento",
    )

    class Meta:
        model = Job
        fields = [
            "client",
            "title",
            "event_type",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "location",
            "description",
            "cache",
            "payment_type",
            "payment_date",
            "payment_total",
            "payment_partial_value",
            "payment_partial_date",
            "payment_remaining_value",
            "payment_remaining_date",
            "status",
            "payment_status",
        ]
        widgets = {
            "client": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                }
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "Título do trabalho",
                }
            ),
            "event_type": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                }
            ),
            "start_time": forms.TimeInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "type": "time",
                }
            ),
            "end_time": forms.TimeInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "type": "time",
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "Local do evento",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "rows": 3,
                    "placeholder": "Descrição",
                }
            ),
            "cache": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                    "onchange": "onPaymentTypeChange(); calculatePaymentTotalFromCache();",
                }
            ),
            "payment_type": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "onchange": "onPaymentTypeChange()",
                }
            ),
            "payment_total": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
            "payment_partial_value": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                    "onchange": "calculatePaymentRemaining()",
                }
            ),
            "payment_remaining_value": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                }
            ),
            "payment_status": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        instance = kwargs.get("instance", None)
        super().__init__(*args, **kwargs)

        # Filtrar clientes apenas da empresa do usuário
        if user and hasattr(user, "account") and user.account:
            self.fields["client"].queryset = user.account.clients.all()
        elif user:
            # Se não tem empresa vinculada, mostra só clientes que ele criou
            self.fields["client"].queryset = user.clients_created.all()

        self.fields["end_date"].required = False
        self.fields["payment_type"].required = False
        self.fields["status"].required = False
        self.fields["payment_status"].required = False
        self.fields["event_type"].required = False
        self.fields["client"].required = True
        self.fields["title"].required = True
        self.order_fields(["client", "event_type", "title"])

        # Definir datas default para pagamento (20 dias após evento) se não for edição
        start_date = None
        if not instance:
            # Check both form initial and field initial
            if self.initial.get("start_date"):
                start_date = self.initial.get("start_date")
            elif self.fields["start_date"].initial:
                start_date = self.fields["start_date"].initial

            if start_date:
                from datetime import timedelta, date

                if isinstance(start_date, str):
                    start_date = date.fromisoformat(start_date)
                payment_date = start_date + timedelta(days=20)
                self.fields["payment_date"].initial = payment_date
                self.fields["payment_partial_date"].initial = payment_date
                self.fields["payment_remaining_date"].initial = payment_date

        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "")
            if self.errors.get(field_name):
                field.widget.attrs["class"] = (
                    f"{current_class} border-red-500 focus:ring-red-500 focus:border-red-500".strip()
                )
