from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages

from .models import Service
from .forms import ServiceForm


class CompanyRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.account:
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden("Você precisa estar associado a uma empresa.")
        return super().dispatch(request, *args, **kwargs)


class ServiceListView(CompanyRequiredMixin, View):
    template_name = "services/list.html"

    def get(self, request):
        company = request.user.account
        services = Service.objects.filter(account=company, is_active=True).order_by(
            "name"
        )
        return render(request, self.template_name, {"services": services})


class ServiceCreateView(CompanyRequiredMixin, View):
    template_name = "services/form.html"

    def get(self, request):
        form = ServiceForm()
        next_url = request.GET.get("next", "")
        return render(request, self.template_name, {"form": form, "next_url": next_url})

    def post(self, request):
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.account = request.user.account
            service.save()

            # Criar notificação
            if request.user.account.notify_on_service_created:
                from base.accounts.models import Notification, NotificationType

                Notification.objects.create(
                    user=request.user,
                    title="Novo serviço criado",
                    message=f"Serviço '{service.name}' foi adicionado",
                    action_url=f"/servicos/",
                    notification_type=NotificationType.SERVICE,
                )

            messages.success(request, "Serviço criado com sucesso!")
            next_url = request.POST.get("next", "")
            if next_url:
                if "?" in next_url:
                    next_url += f"&services={service.pk}"
                else:
                    next_url += f"?services={service.pk}"
                return redirect(next_url)
            return redirect("services:list")
        next_url = request.GET.get("next", "")
        return render(request, self.template_name, {"form": form, "next_url": next_url})


class ServiceUpdateView(CompanyRequiredMixin, View):
    template_name = "services/form.html"

    def get(self, request, pk):
        service = get_object_or_404(Service, pk=pk, account=request.user.account)
        form = ServiceForm(instance=service)
        return render(request, self.template_name, {"form": form, "object": service})

    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk, account=request.user.account)
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço atualizado com sucesso!")
            return redirect("services:list")
        return render(request, self.template_name, {"form": form, "object": service})


class ServiceDeleteView(CompanyRequiredMixin, View):
    template_name = "services/confirm_delete.html"

    def get(self, request, pk):
        service = get_object_or_404(Service, pk=pk, account=request.user.account)
        return render(request, self.template_name, {"service": service})

    def post(self, request, pk):
        service = get_object_or_404(Service, pk=pk, account=request.user.account)
        service.is_active = False
        service.save()
        messages.success(request, "Serviço excluído (inativado) com sucesso!")
        return redirect("services:list")
