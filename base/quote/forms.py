from django import forms
from decimal import Decimal, InvalidOperation
from .models import Quote, QuoteExpense


class QuoteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        created_by = kwargs.pop("created_by", None)
        hide_status = kwargs.pop("hide_status", False)
        super().__init__(*args, **kwargs)
        self.fields["client"].required = False
        if created_by:
            if created_by.is_superuser:
                pass
            else:
                self.fields["client"].queryset = self.fields["client"].queryset.filter(
                    created_by=created_by
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

        if hide_status and "status" in self.fields:
            self.fields["status"].widget = forms.HiddenInput()
            self.fields["status"].required = False
            self.fields["status"].initial = "created"

    def _parse_decimal_input(self, raw_value):
        if raw_value in (None, ""):
            return None

        value = str(raw_value).strip().replace(" ", "")
        if "," in value:
            value = value.replace(".", "").replace(",", ".")

        try:
            return Decimal(value)
        except (InvalidOperation, ValueError):
            raise forms.ValidationError("Informe um número válido.")

    def clean_hourly_rate(self):
        raw = self.data.get("hourly_rate")
        parsed = self._parse_decimal_input(raw)
        if parsed is None:
            return self.cleaned_data.get("hourly_rate")
        return parsed

    def clean_work_hours(self):
        raw = self.data.get("work_hours")
        parsed = self._parse_decimal_input(raw)
        if parsed is None:
            return self.cleaned_data.get("work_hours")
        if parsed <= 0:
            raise forms.ValidationError("Informe uma quantidade de diárias maior que zero.")
        if parsed != parsed.to_integral_value():
            raise forms.ValidationError("Quantidade de diárias deve ser um número inteiro.")
        return parsed

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
                    "step": "1",
                    "min": "1",
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
