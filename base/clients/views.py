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

User = get_user_model()


class ClientListView(LoginRequiredMixin, View):
    template_name = "clients/list.html"

    def get(self, request):
        user = request.user
        is_superuser = user.is_superuser

        if is_superuser:
            clients = Client.objects.filter(is_active=True).order_by("name")
        else:
            clients = Client.objects.filter(created_by=user, is_active=True).order_by("name")

        query = request.GET.get("q", "")
        if query:
            clients = clients.filter(
                Q(name__icontains=query)
                | Q(email__icontains=query)
                | Q(phone__icontains=query)
            )

        return render(
            request,
            self.template_name,
            {
                "clients": clients,
                "query": query,
                "is_superuser": is_superuser,
            },
        )


class ClientCreateView(LoginRequiredMixin, View):
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
            client.created_by = request.user
            client.save()

            from base.accounts.models import Notification, NotificationType

            Notification.objects.create(
                user=request.user,
                title="Novo cliente criado",
                message=f"Cliente '{client.name}' foi adicionado",
                action_url=f"/app/clientes/{client.pk}/",
                notification_type=NotificationType.CLIENT,
            )

            messages.success(request, "Cliente criado com sucesso!")
            return redirect("clients:list")
        return render(request, self.template_name, {"form": form})


class ClientQuickCreateView(LoginRequiredMixin, View):
    def post(self, request):
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()

            return JsonResponse({"id": client.pk, "name": client.name})
        return JsonResponse({"error": "Erro ao criar cliente"}, status=400)


class ClientUpdateView(LoginRequiredMixin, View):
    template_name = "clients/form.html"

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk, created_by=request.user, is_active=True)
        form = ClientForm(instance=client)
        return render(request, self.template_name, {"form": form, "object": client})

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk, created_by=request.user, is_active=True)
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente atualizado com sucesso!")
            return redirect("clients:list")
        return render(request, self.template_name, {"form": form, "object": client})


class ClientDetailView(LoginRequiredMixin, TemplateView):
    template_name = "clients/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = get_object_or_404(
            Client, pk=self.kwargs["pk"], created_by=self.request.user
        )
        context["client"] = client
        context["jobs"] = client.jobs.filter(is_active=True)
        return context


class ClientDeleteView(LoginRequiredMixin, View):
    template_name = "clients/confirm_delete.html"

    def get(self, request, pk):
        client = get_object_or_404(Client, pk=pk, created_by=request.user, is_active=True)
        return render(request, self.template_name, {"client": client})

    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk, created_by=request.user, is_active=True)
        client.delete()
        messages.success(request, "Cliente excluído com sucesso!")
        return redirect("clients:list")
