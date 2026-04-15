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
