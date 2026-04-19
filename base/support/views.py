from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.utils import timezone

from .models import SupportMessage
from .forms import SupportMessageForm


class SupportContactView(View):
    template_name = "support/contact.html"

    def get(self, request):
        form = SupportMessageForm(
            user=request.user if request.user.is_authenticated else None
        )
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SupportMessageForm(
            request.POST, user=request.user if request.user.is_authenticated else None
        )

        if form.is_valid():
            support_msg = form.save(commit=False)
            if request.user.is_authenticated:
                support_msg.user = request.user
            support_msg.save()

            messages.success(
                request,
                "Mensagem enviada com sucesso! Nossa equipe retornará em breve.",
            )
            return redirect("support:success")

        return render(request, self.template_name, {"form": form})


class SupportSuccessView(View):
    template_name = "support/success.html"

    def get(self, request):
        return render(request, self.template_name)


class SupportAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class SupportAdminListView(SupportAdminMixin, View):
    template_name = "support/admin_list.html"

    def get(self, request):
        messages_list = (
            SupportMessage.objects.all()
            .select_related("user", "responded_by")
            .order_by("-created_at")
        )

        unread_count = messages_list.filter(is_read=False).count()

        return render(
            request,
            self.template_name,
            {
                "messages": messages_list,
                "unread_count": unread_count,
            },
        )


class SupportAdminDetailView(SupportAdminMixin, View):
    template_name = "support/admin_detail.html"

    def get(self, request, pk):
        msg = get_object_or_404(
            SupportMessage.objects.select_related("user", "responded_by"), pk=pk
        )

        if not msg.is_read:
            msg.is_read = True
            msg.save()
            from base.core.context_processors import clear_support_cache

            clear_support_cache()

        return render(request, self.template_name, {"message": msg})

    def post(self, request, pk):
        msg = get_object_or_404(SupportMessage, pk=pk)
        response_text = request.POST.get("response", "").strip()

        if response_text:
            msg.response = response_text
            msg.responded_at = timezone.now()
            msg.responded_by = request.user
            msg.save()

            from base.core.emails import send_support_reply
            from base.core.context_processors import clear_support_cache

            send_support_reply(msg)
            clear_support_cache()

            messages.success(request, "Resposta enviada por email!")

        return redirect("support:admin_detail", pk=pk)
