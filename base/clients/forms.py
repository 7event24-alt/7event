from django import forms
from django.contrib.auth import get_user_model
from .models import Client

User = get_user_model()


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "name",
            "email",
            "phone",
            "document",
            "address",
            "notes",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                    "placeholder": "Nome do cliente",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                    "placeholder": "email@exemplo.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                    "placeholder": "(00) 00000-0000",
                    "data-mask": "phone",
                    "maxlength": "15",
                }
            ),
            "document": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                    "placeholder": "CPF ou CNPJ",
                    "data-mask": "cpf-cnpj",
                    "maxlength": "18",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                    "rows": 3,
                    "placeholder": "Endereço completo",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                    "rows": 3,
                    "placeholder": "Observações",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["phone"].required = True

        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "")
            if self.errors.get(field_name):
                field.widget.attrs["class"] = (
                    f"{current_class} border-red-500 focus:ring-red-500 focus:border-red-500".strip()
                )
