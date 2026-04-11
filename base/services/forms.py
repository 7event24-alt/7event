from django import forms
from .models import Service


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = [
            "name",
            "description",
            "estimated_duration_hours",
            "hourly_rate",
            "typical_expenses",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "Nome do serviço",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "rows": 3,
                }
            ),
            "estimated_duration_hours": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0",
                    "step": "1",
                }
            ),
            "hourly_rate": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
            "typical_expenses": forms.NumberInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm",
                    "placeholder": "0,00",
                    "step": "0.01",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "")
            if self.errors.get(field_name):
                field.widget.attrs["class"] = (
                    f"{current_class} border-red-500 focus:ring-red-500 focus:border-red-500".strip()
                )
