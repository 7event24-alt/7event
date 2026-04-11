from django import forms
from .models import Quote, QuoteExpense, QuoteService
from base.services.models import Service


class QuoteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        account = kwargs.pop("account", None) or kwargs.pop("company", None)
        super().__init__(*args, **kwargs)
        self.fields["client"].required = False
        if account:
            self.fields["client"].queryset = self.fields["client"].queryset.filter(
                account=account
            )

        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "input")
            if "input" in current_class:
                current_class = current_class.replace(
                    "input",
                    "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                )
            else:
                current_class = f"w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm {current_class}"
            if self.errors.get(field_name):
                current_class += (
                    " border-red-500 focus:ring-red-500 focus:border-red-500"
                )
            field.widget.attrs["class"] = current_class.strip()

    class Meta:
        model = Quote
        fields = [
            "client",
            "title",
            "description",
            "hourly_rate",
            "work_hours",
            "notes",
            "status",
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
                    "placeholder": "Título do orçamento",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "rows": 3,
                }
            ),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
            "work_hours": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0",
                    "step": "0.01",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "rows": 3,
                }
            ),
        }


class QuoteServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        account = kwargs.pop("account", None) or kwargs.pop("company", None)
        super().__init__(*args, **kwargs)
        if account:
            self.fields["service"].queryset = Service.objects.filter(account=account)

        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "input")
            if "input" in current_class:
                current_class = current_class.replace(
                    "input",
                    "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                )
            else:
                current_class = f"w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm {current_class}"
            if self.errors.get(field_name):
                current_class += (
                    " border-red-500 focus:ring-red-500 focus:border-red-500"
                )
            field.widget.attrs["class"] = current_class.strip()

    class Meta:
        model = QuoteService
        fields = ["service", "quantity", "custom_price"]
        widgets = {
            "service": forms.Select(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "min": 1,
                    "value": 1,
                }
            ),
            "custom_price": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "Deixe vazio para usar padrão",
                    "step": "0.01",
                }
            ),
        }


class QuoteExpenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "input")
            if "input" in current_class:
                current_class = current_class.replace(
                    "input",
                    "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                )
            else:
                current_class = f"w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm {current_class}"
            if self.errors.get(field_name):
                current_class += (
                    " border-red-500 focus:ring-red-500 focus:border-red-500"
                )
            field.widget.attrs["class"] = current_class.strip()

    class Meta:
        model = QuoteExpense
        fields = ["description", "quantity", "unit_price"]
        widgets = {
            "description": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "Descrição da despesa",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "1",
                    "step": "1",
                }
            ),
            "unit_price": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
        }
