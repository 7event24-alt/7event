from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages

from .models import Service
from .forms import ServiceForm


class ServiceListView(LoginRequiredMixin, View):
    template_name = "services/list.html"

    def get(self, request):
        user = request.user
        if user.is_superuser:
            services = Service.objects.filter(is_active=True).order_by("name")
        else:
            services = Service.objects.filter(created_by=user, is_active=True).order_by(
                "name"
            )
        return render(request, self.template_name, {"services": services})


class ServiceCreateView(LoginRequiredMixin, View):
    template_name = "services/form.html"

    def get(self, request):
        form = ServiceForm()
        next_url = request.GET.get("next", "")
        return render(request, self.template_name, {"form": form, "next_url": next_url})

    def post(self, request):
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.created_by = request.user
            service.save()

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


class ServiceUpdateView(LoginRequiredMixin, View):
    template_name = "services/form.html"

    def get(self, request, pk):
        user = request.user
        if user.is_superuser:
            service = get_object_or_404(Service, pk=pk, is_active=True)
        else:
            service = get_object_or_404(Service, pk=pk, created_by=user, is_active=True)
        form = ServiceForm(instance=service)
        return render(request, self.template_name, {"form": form, "object": service})

    def post(self, request, pk):
        user = request.user
        if user.is_superuser:
            service = get_object_or_404(Service, pk=pk, is_active=True)
        else:
            service = get_object_or_404(Service, pk=pk, created_by=user, is_active=True)
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, "Serviço atualizado com sucesso!")
            return redirect("services:list")
        return render(request, self.template_name, {"form": form, "object": service})


class ServiceDeleteView(LoginRequiredMixin, View):
    template_name = "services/confirm_delete.html"

    def get(self, request, pk):
        user = request.user
        if user.is_superuser:
            service = get_object_or_404(Service, pk=pk, is_active=True)
        else:
            service = get_object_or_404(Service, pk=pk, created_by=user, is_active=True)
        return render(request, self.template_name, {"service": service})

    def post(self, request, pk):
        user = request.user
        if user.is_superuser:
            service = get_object_or_404(Service, pk=pk, is_active=True)
        else:
            service = get_object_or_404(Service, pk=pk, created_by=user, is_active=True)
        service.is_active = False
        service.save()
        messages.success(request, "Serviço excluído (inativado) com sucesso!")
        return redirect("services:list")