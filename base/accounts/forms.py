from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from .models import User, Account, ProfessionalRole, Plan, AccountType


def add_widget_classes(field, error_class=""):
    """Adiciona classes Tailwind consistentes aos widgets"""
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
    company_name = forms.CharField(
        max_length=200,
        required=False,
        label="Nome da Empresa/Organização",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Nome da sua empresa ou organização",
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

    def clean_company_name(self):
        return self.cleaned_data.get("company_name", "")

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
        from .models import Account, Plan, AccountType
        from django.utils.text import slugify
        import uuid

        user = super().save(commit=False)

        # Normalizar telefone: remover máscara
        if user.phone:
            import re

            user.phone = re.sub(r"\D", "", user.phone)

        # Criar usuário inativo até verificar o email
        user.is_active = False
        user.verification_token = secrets.token_urlsafe(32)

        if commit:
            user.save()

            company_name = self.cleaned_data.get("company_name", "").strip()

            # Se não informar empresa, usa o nome do usuário (MEI/autônomo)
            if not company_name:
                company_name = (
                    f"{user.first_name} {user.last_name}".strip()
                    or user.email.split("@")[0]
                )

            # Fallback final
            if not company_name or not company_name.strip():
                company_name = f"Usuario-{user.id}"

            base_slug = slugify(company_name)
            if not base_slug:
                base_slug = f"company-{uuid.uuid4().hex[:8]}"

            # Garantir slug único
            slug = base_slug
            counter = 1
            while Account.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            plan = Plan.get_default()

            # Criar empresa
            account = Account.objects.create(
                name=company_name or "Minha Empresa",
                slug=slug,
                account_type=AccountType.COMPANY,
                plan=plan,
                is_active=True,
            )

            # Vincular usuário à empresa
            user.account = account
            user.save()

        return user


class AccountAdminForm(forms.ModelForm):
    name = forms.CharField(
        label="Nome da Conta",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "Nome da empresa/cliente",
            }
        ),
    )
    slug = forms.SlugField(
        label="Slug (URL)",
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "nome-empresa",
            }
        ),
    )
    cnpj = forms.CharField(
        label="CNPJ",
        required=False,
        max_length=18,
        widget=forms.TextInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "00.000.000/0001-00",
                "data-mask": "cnpj",
                "maxlength": "18",
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
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "placeholder": "email@empresa.com",
            }
        ),
    )
    address = forms.CharField(
        label="Endereço",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm",
                "rows": 3,
            }
        ),
    )
    account_type = forms.ChoiceField(
        label="Tipo de Conta",
        choices=[("", "---------")] + list(AccountType.choices),
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
            }
        ),
    )
    plan = forms.ModelChoiceField(
        label="Plano",
        queryset=None,
        empty_label="---------",
        widget=forms.Select(
            attrs={
                "class": "w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
            }
        ),
    )
    is_active = forms.BooleanField(
        label="Conta Ativa",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
            }
        ),
    )

    class Meta:
        model = Account
        fields = (
            "account_type",
            "name",
            "slug",
            "cnpj",
            "phone",
            "email",
            "address",
            "plan",
            "is_active",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].queryset = Plan.objects.all()


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
    is_admin = forms.BooleanField(
        label="Usuário é administrador da conta",
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "w-4 h-4 text-primary border-gray-300 rounded focus:ring-primary"
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

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone", "role", "photo")

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


class PasswordChangeForm(forms.ModelForm):
    password = forms.CharField(
        label="Nova Senha",
        widget=forms.PasswordInput(attrs={"class": "input"}),
    )

    class Meta:
        model = User
        fields = ()
