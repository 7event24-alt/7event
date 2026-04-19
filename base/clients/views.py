from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from .models import Client
from .forms import ClientForm
from base.accounts.models import Company

User = get_user_model()


class CompanyRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login

            return redirect_to_login(request.get_full_path())

        if not request.user.account:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Você precisa estar associado a uma empresa.")
        return super().dispatch(request, *args, **kwargs)


class ClientListView(CompanyRequiredMixin, View):
    template_name = "clients/list.html"

    def get(self, request):
        company = request.user.account
        user = request.user
        is_superuser = user.is_superuser

        if is_superuser:
            clients = Client.objects.filter(account=company).order_by("name")
        else:
            clients = Client.objects.filter(account=company, created_by=user).order_by(
                "name"
            )

        query = request.GET.get("q", "")
        if query:
            clients = clients.filter(
                Q(name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
            )

        user_filter = request.GET.get("user", "")
        if user_filter:
            clients = clients.filter(created_by_id=user_filter)

        users = []
        if is_superuser:
            users = company.users.all()

        return render(
            request,
            self.template_name,
            {
                "clients": clients,
                "query": query,
                "user_filter": user_filter,
                "users": users,
                "is_superuser": is_superuser,
            },
        )


class ClientCreateView(CompanyRequiredMixin, View):
    template_name = "clients/form.html"

    def dispatch(self, request, *args, **kwargs):
        from base.core.plan_check import check_plan_limit
        from .models import Client

        return check_plan_limit(Client, "max_clients")(super().dispatch)(
            request, *args, **kwargs
        )

    def get(self, request):
        form = ClientForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.account = request.user.account
            client.created_by = request.user
            client.save()

            if request.user.account.notify_on_client_created:
                from base.accounts.models import Notification, NotificationType

                Notification.objects.create(
                    user=request.user,
                    title="Novo cliente criado",
                    message=f"Cliente '{client.name}' foi adicionado",
                    action_url=f"/clientes/{client.pk}/",
                    notification_type=NotificationType.CLIENT,
                )

            # Enviar push notification via HTTP to FCM
            import logging
            logger = logging.getLogger(__name__)
            logger.error("=== Push: Starting ===")
            
            try:
                import requests
                import os
                
                # Get service account key
                service_account_path = os.path.join(settings.BASE_DIR, 'event-b2848-firebase-adminsdk-fbsvc-96ece007ee.json')
                logger.error(f"Push: SA path: {service_account_path}, exists: {os.path.exists(service_account_path)}")
                
                if not os.path.exists(service_account_path):
                    logger.error("Push: Service account not found")
                
                # Ler service account
                import google.auth.transport.requests as google_requests
                from oauth2client.service_account import ServiceAccountCredentials
                
                credentials = ServiceAccountCredentials.from_json_keyfile_name(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/firebase.messaging']
                )
                
                access_token_info = credentials.get_access_token()
                access_token = access_token_info.access_token
                
                subscriptions = []
                try:
                    with open('/tmp/push_subscriptions.txt', 'r') as f:
                        for line in f:
                            if line.strip():
                                subscriptions.append(json.loads(line.strip()))
                except Exception as e:
                    logger.error(f"Push: Error reading: {e}")
                
                logger.error(f"Push: Found {len(subscriptions)} subscriptions")
                
                if subscriptions:
                    for sub in subscriptions:
                        endpoint = sub.get('endpoint', '')
                        if 'fcm.googleapis.com' in endpoint and ':' in endpoint:
                            # Extract token from endpoint: https://fcm.googleapis.com/fcm/send/{token}
                            token = endpoint.split('/send/')[-1]
                            
                            logger.error(f"Push: Token: {token[:50]}...")
                            
                            # Send via FCM HTTP v1 API
                            url = f"https://fcm.googleapis.com/v1/projects/event-b2848/messages:send"
                            headers = {
                                "Authorization": f"Bearer {access_token}",
                                "Content-Type": "application/json"
                            }
                            payload = {
                                "message": {
                                    "token": token,
                                    "notification": {
                                        "title": "Novo Cliente",
                                        "body": f"'{client.name}' foi adicionado"
                                    }
                                }
                            }
                            
                            try:
                                resp = requests.post(url, headers=headers, json=payload)
                                logger.error(f"Push: Response {resp.status_code}: {resp.text[:200]}")
                            except Exception as e:
                                logger.error(f"Push: HTTP error: {e}")
                                
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Push: Outer error: {e}")

            messages.success(request, "Cliente criado com sucesso!")
            return redirect("clients:list")
        return render(request, self.template_name, {"form": form})


class ClientQuickCreateView(CompanyRequiredMixin, View):
    def post(self, request):
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.account = request.user.account
            client.created_by = request.user
            client.save()

            if request.user.account.notify_on_client_created:
                from base.accounts.models import Notification, NotificationType

                Notification.objects.create(
                    user=request.user,
                    title="Novo cliente criado",
                    message=f"Cliente '{client.name}' foi adicionado",
                    action_url=f"/clientes/{client.pk}/",
                    notification_type=NotificationType.CLIENT,
                )

            return JsonResponse({"id": client.pk, "name": client.name})
        return JsonResponse({"error": "Erro ao criar cliente"}, status=400)


class ClientUpdateView(CompanyRequiredMixin, View):
    template_name = "clients/form.html"

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk, account=request.user.account)
        form = ClientForm(instance=client)
        return render(request, self.template_name, {"form": form, "object": client})

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk, account=request.user.account)
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado com sucesso!")
            return redirect("clients:list")
        return render(request, self.template_name, {"form": form, "object": client})


class ClientDetailView(CompanyRequiredMixin, TemplateView):
    template_name = "clients/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = get_object_or_404(
            Client, pk=self.kwargs["pk"], account=self.request.user.account
        )
        context["client"] = client
        context["jobs"] = client.jobs.all()
        return context


class ClientDeleteView(CompanyRequiredMixin, View):
    template_name = "clients/confirm_delete.html"

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk, account=request.user.account)
        return render(request, self.template_name, {"client": client})

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk, account=request.user.account)
        client.delete()
        messages.success(request, "Cliente excluído com sucesso!")
        return redirect("clients:list")
