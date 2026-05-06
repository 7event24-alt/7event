from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from .models import User, ProfessionalRole, Plan


def add_widget_classes(field, error_class=""):
    base_classes = "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
    if error_class:
        base_classes = (
            base_classes.replace("border-gray-300", "border-red-500")
            .replace("focus:ring-primary", "focus:ring-red-500")
            .replace("focus:border-primary", "focus:border-red-500")
        )
    return base_classes


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nome",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Seu nome",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Sobrenome",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Seu sobrenome",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "seu@email.com",
            }
        ),
    )
    phone = forms.CharField(
        max_length=15,
        required=True,
        label="Telefone",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "(00) 00000-0000",
                "data-mask": "phone",
                "maxlength": "15",
            }
        ),
    )
    role = forms.ChoiceField(
        required=False,
        label="Profissão/Cargo",
        choices=list(ProfessionalRole.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
            }
        ),
    )
    legal_name = forms.CharField(
        max_length=200,
        required=False,
        label="Nome Fantasia / Razão Social",
        initial="Conta Profissional",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Nome da sua empresa ou organização",
                "value": "Conta Profissional",
            }
        ),
    )
    cnpj = forms.CharField(
        max_length=18,
        required=False,
        label="CNPJ",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "00.000.000/0001-00",
                "data-mask": "cnpj",
                "maxlength": "18",
            }
        ),
    )
    full_name = forms.CharField(
        max_length=200,
        required=False,
        label="Nome Completo",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Seu nome completo",
            }
        ),
    )
    cpf = forms.CharField(
        max_length=14,
        required=False,
        label="CPF",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "000.000.000-00",
                "data-mask": "cpf",
                "maxlength": "14",
            }
        ),
    )
    rg = forms.CharField(
        max_length=20,
        required=False,
        label="RG",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "00.000.000-0",
            }
        ),
    )
    bio = forms.CharField(
        required=False,
        label="Biografia",
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Conte um pouco sobre você...",
                "rows": "3",
            }
        ),
    )
    skills = forms.CharField(
        max_length=500,
        required=False,
        label="Habilidades (separadas por vírgula)",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "ex: DJ, Iluminação, Som, Produção",
            }
        ),
    )
    portfolio_url = forms.URLField(
        required=False,
        label="URL do Portfólio",
        widget=forms.URLInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "https://seuportfolio.com",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "legal_name",
            "cnpj",
            "full_name",
            "cpf",
            "rg",
            "bio",
            "skills",
            "portfolio_url",
            "password1",
            "password2",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Senha",
            }
        )
        self.fields["password2"].widget.attrs.update(
            {
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Confirmar senha",
            }
        )
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{current_class}".strip()

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            return email

        from django.contrib.auth import get_user_model

        User = get_user_model()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Este email já está cadastrado em outra conta. "
                "Entre em contato com o suporte para recuperar seu acesso."
            )
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return phone

        import re

        phone_normalized = re.sub(r"\D", "", phone)

        if not phone_normalized:
            return phone

        from django.contrib.auth import get_user_model

        User = get_user_model()

        for user in User.objects.filter(phone__isnull=False).exclude(phone=""):
            if user.phone:
                user_phone_normalized = re.sub(r"\D", "", user.phone)
                if user_phone_normalized == phone_normalized:
                    raise forms.ValidationError(
                        "Este telefone já está cadastrado em outra conta. "
                        "Entre em contato com o suporte para recuperar seu acesso."
                    )
        return phone

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("As senhas não conferem.")

            password_validation.validate_password(password2, self.instance)

        return password2

    def save(self, commit=True):
        import secrets
        import re

        user = super().save(commit=False)

        user.phone = re.sub(r"\D", "", user.phone) if user.phone else ""

        user.is_active = False
        user.verification_token = secrets.token_urlsafe(32)

        if commit:
            user.save()

        return user


class UserAdminCreationForm(forms.ModelForm):
    first_name = forms.CharField(
        label="Nome",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Nome",
            }
        ),
    )
    last_name = forms.CharField(
        label="Sobrenome",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Sobrenome",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "email@exemplo.com",
            }
        ),
    )
    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "nome de usuário",
            }
        ),
    )
    phone = forms.CharField(
        label="Telefone",
        required=False,
        max_length=15,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "(00) 00000-0000",
                "data-mask": "phone",
                "maxlength": "15",
            }
        ),
    )
    password1 = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Senha",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmar Senha",
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Confirmar senha",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username", "phone")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("As senhas não conferem.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nome",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Seu nome",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Sobrenome",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Seu sobrenome",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "seu@email.com",
            }
        ),
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        label="Telefone",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "(00) 00000-0000",
                "data-mask": "phone",
                "maxlength": "15",
            }
        ),
    )
    role = forms.ChoiceField(
        required=False,
        label="Profissão/Cargo",
        choices=list(ProfessionalRole.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
            }
        ),
    )
    photo = forms.ImageField(
        required=False,
        label="Foto de Perfil",
        widget=forms.FileInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "accept": "image/*",
            }
        ),
    )
    full_name = forms.CharField(
        max_length=200,
        required=False,
        label="Nome Completo",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Seu nome completo",
            }
        ),
    )
    cpf = forms.CharField(
        max_length=14,
        required=False,
        label="CPF",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "000.000.000-00",
                "data-mask": "cpf",
                "maxlength": "14",
            }
        ),
    )
    rg = forms.CharField(
        max_length=20,
        required=False,
        label="RG",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "00.000.000-0",
            }
        ),
    )
    bio = forms.CharField(
        required=False,
        label="Biografia",
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Conte um pouco sobre você...",
                "rows": "3",
            }
        ),
    )
    skills = forms.CharField(
        max_length=500,
        required=False,
        label="Habilidades (separadas por vírgula)",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "ex: DJ, Iluminação, Som, Produção",
            }
        ),
    )
    portfolio_url = forms.URLField(
        required=False,
        label="URL do Portfólio",
        widget=forms.URLInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "https://seuportfolio.com",
            }
        ),
    )
    show_sensitive_data = forms.BooleanField(
        required=False,
        label="Permitir que contratantes (Business) vejam meus documentos (CPF/RG) após aceite do trabalho",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-primary focus:ring-primary border-gray-300 rounded",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "first_name", "last_name", "email", "phone", "role", "photo",
            "full_name", "cpf", "rg", "bio", "skills", "portfolio_url", "show_sensitive_data"
        )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            return email

        from django.contrib.auth import get_user_model

        User = get_user_model()

        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Este email já está cadastrado em outra conta.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return phone

        import re

        phone_normalized = re.sub(r"\D", "", phone)

        if not phone_normalized:
            return phone

        from django.contrib.auth import get_user_model

        User = get_user_model()

        for user in (
            User.objects.filter(phone__isnull=False)
            .exclude(phone="")
            .exclude(pk=self.instance.pk)
        ):
            if user.phone:
                user_phone_normalized = re.sub(r"\D", "", user.phone)
                if user_phone_normalized == phone_normalized:
                    raise forms.ValidationError(
                        "Este telefone já está cadastrado em outra conta."
                    )

        self.cleaned_data["phone"] = phone_normalized
        return phone_normalized


class PersonalInfoForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nome",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Seu nome",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Sobrenome",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Seu sobrenome",
            }
        ),
    )
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "seu@email.com",
            }
        ),
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        label="Telefone",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "(00) 00000-0000",
                "data-mask": "phone",
                "maxlength": "15",
            }
        ),
    )
    cpf = forms.CharField(
        max_length=14,
        required=False,
        label="CPF",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "000.000.000-00",
                "data-mask": "cpf",
                "maxlength": "14",
            }
        ),
    )
    rg = forms.CharField(
        max_length=20,
        required=False,
        label="RG",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "00.000.000-0",
            }
        ),
    )
    pix_key = forms.CharField(
        max_length=255,
        required=False,
        label="Chave PIX",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "CPF, telefone, email ou chave aleatória",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "cpf", "rg", "pix_key")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if not email:
            return email

        from django.contrib.auth import get_user_model

        User = get_user_model()

        if (
            User.objects.filter(email__iexact=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("Este email já está cadastrado em outra conta.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if not phone:
            return phone

        import re

        phone_normalized = re.sub(r"\D", "", phone)

        if not phone_normalized:
            return phone

        from django.contrib.auth import get_user_model

        User = get_user_model()

        for user in (
            User.objects.filter(phone__isnull=False)
            .exclude(phone="")
            .exclude(pk=self.instance.pk)
        ):
            if user.phone:
                user_phone_normalized = re.sub(r"\D", "", user.phone)
                if user_phone_normalized == phone_normalized:
                    raise forms.ValidationError(
                        "Este telefone já está cadastrado em outra conta."
                    )

        self.cleaned_data["phone"] = phone_normalized
        return phone_normalized

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-preencher full_name com first_name + last_name
        instance.full_name = f"{self.cleaned_data.get('first_name', '')} {self.cleaned_data.get('last_name', '')}".strip()
        if commit:
            instance.save()
        return instance


class ProfessionalInfoForm(forms.ModelForm):
    bio = forms.CharField(
        required=False,
        label="Biografia",
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Conte um pouco sobre você...",
                "rows": "3",
            }
        ),
    )
    skills = forms.CharField(
        max_length=500,
        required=False,
        label="Habilidades (separadas por vírgula)",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "ex: DJ, Iluminação, Som, Produção",
            }
        ),
    )
    portfolio_url = forms.URLField(
        required=False,
        label="URL do Portfólio",
        widget=forms.URLInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "https://seuportfolio.com",
            }
        ),
    )
    role = forms.ChoiceField(
        required=False,
        label="Profissão/Cargo",
        choices=list(ProfessionalRole.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
            }
        ),
    )
    photo = forms.ImageField(
        required=False,
        label="Foto de Perfil",
        widget=forms.FileInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "accept": "image/*",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("bio", "skills", "portfolio_url", "role", "photo")


class PrivacyForm(forms.ModelForm):
    show_sensitive_data = forms.BooleanField(
        required=False,
        label="Permitir que contratantes (Business) vejam meus documentos (CPF/RG) após aceite do trabalho",
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-primary focus:ring-primary border-gray-300 rounded",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("show_sensitive_data",)


class PasswordChangeForm(forms.ModelForm):
    password = forms.CharField(
        label="Nova Senha",
        widget=forms.PasswordInput(attrs={"class": "input"}),
    )

    class Meta:
        model = User
        fields = ()
