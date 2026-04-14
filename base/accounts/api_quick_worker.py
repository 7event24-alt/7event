from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

User = get_user_model()


@method_decorator(csrf_exempt, name="dispatch")
class QuickWorkerView(View):
    def post(self, request):
        import json

        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({"success": False, "error": "Dados inválidos"})

        first_name = data.get("first_name", "").strip()
        email = data.get("email", "").strip()
        role = data.get("role", "").strip()

        if not first_name or not email:
            return JsonResponse(
                {"success": False, "error": "Nome e email são obrigatórios"}
            )

        if not hasattr(request.user, "account") or not request.user.account:
            return JsonResponse(
                {"success": False, "error": "Você não tem uma empresa associada"}
            )

        # Verificar se email já existe na empresa
        if User.objects.filter(email=email, account=request.user.account).exists():
            return JsonResponse(
                {"success": False, "error": "Este email já está cadastrado na equipe"}
            )

        import uuid

        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=data.get("last_name", "").strip(),
            account=request.user.account,
            role=role,
            is_active=True,
            invite_token=uuid.uuid4().hex,
            invited_by=request.user,
        )

        return JsonResponse(
            {
                "success": True,
                "worker": {
                    "id": user.id,
                    "name": user.get_full_name(),
                    "email": user.email,
                    "role": user.role,
                },
            }
        )


quick_worker = QuickWorkerView.as_view()
