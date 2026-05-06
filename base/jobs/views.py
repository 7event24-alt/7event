from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views import View
from django.contrib import messages
from django.utils import timezone
import weasyprint

from .models import Job, EventType, JobStatus, PaymentType, PaymentStatusJob, JobStaff, JobStaffStatus
from base.accounts.models import ProfessionalRole, PlanType
from base.clients.models import Client


class JobListView(LoginRequiredMixin, View):
    template_name = "jobs/list.html"

    def get(self, request):
        user = request.user

        if user.is_superuser:
            jobs = Job.objects.filter(is_active=True)
        else:
            jobs = Job.objects.filter(
                Q(created_by=user) | Q(job_staff__professional=user),
                is_active=True
            ).distinct()

        jobs = jobs.select_related("client", "created_by").prefetch_related("job_staff").order_by("-start_date")

        query = request.GET.get("q", "")
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query)
                | Q(client__name__icontains=query)
                | Q(location__icontains=query)
            )

        status_filter = request.GET.get("status", "")
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        payment_filter = request.GET.get("payment_status", "")
        if payment_filter:
            jobs = jobs.filter(payment_status=payment_filter)

        # For staff members, calculate individual cache value
        jobs_with_cache = []
        for job in jobs:
            is_owner = job.created_by == user
            is_staff = job.job_staff.filter(professional=user).exists()
            
            if is_staff and not is_owner:
                # Show individual cache value for staff
                staff_record = job.job_staff.filter(professional=user).first()
                job.display_cache = staff_record.cache_value if staff_record else 0
            else:
                # Show total cache for owners
                job.display_cache = job.cache
            jobs_with_cache.append(job)

        return render(
            request,
            self.template_name,
            {
                "jobs": jobs_with_cache,
                "query": query,
                "status_filter": status_filter,
                "payment_filter": payment_filter,
                "job_statuses": JobStatus.choices,
                "payment_statuses": PaymentStatusJob.choices,
            },
        )


class JobCreateView(LoginRequiredMixin, View):
    template_name = "jobs/form.html"

    def get(self, request):
        from .forms import JobForm
        from datetime import datetime

        form = JobForm(user=request.user)
        initial_date = request.GET.get("date")
        initial_client = request.GET.get("client")
        initial_title = request.GET.get("title")
        initial_description = request.GET.get("description")
        initial_cache = request.GET.get("cache")
        if initial_date:
            try:
                dt = datetime.strptime(initial_date, "%Y-%m-%d")
                form.fields["start_date"].initial = dt.date()
            except ValueError:
                pass

        if initial_client:
            form.fields["client"].initial = initial_client
        if initial_title:
            form.fields["title"].initial = initial_title
        if initial_description:
            form.fields["description"].initial = initial_description
        if initial_cache:
            form.fields["cache"].initial = initial_cache

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "initial_date": initial_date,
            },
        )

    def post(self, request):
        from .forms import JobForm

        form = JobForm(request.POST, user=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()

            from base.accounts.models import Notification, NotificationType

            Notification.objects.create(
                user=request.user,
                title="Novo trabalho criado",
                message=f"Trabalho '{job.title}' foi criado com sucesso",
                action_url=f"/app/trabalhos/{job.pk}/",
                notification_type=NotificationType.JOB,
            )

            messages.success(request, "Trabalho criado com sucesso!")
            return redirect("jobs:detail", pk=job.pk)

        return render(
            request,
            self.template_name,
            {
                "form": form,
            },
        )


class JobUpdateView(LoginRequiredMixin, View):
    template_name = "jobs/form.html"

    def get(self, request, pk):
        from .forms import JobForm

        job = get_object_or_404(Job, pk=pk, created_by=request.user, is_active=True)
        form = JobForm(instance=job, user=request.user)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": job,
            },
        )

    def post(self, request, pk):
        from .forms import JobForm

        job = get_object_or_404(Job, pk=pk, created_by=request.user, is_active=True)
        form = JobForm(request.POST, instance=job, user=request.user)
        if form.is_valid():
            form.save()

            messages.success(request, "Trabalho atualizado com sucesso!")
            return redirect("jobs:detail", pk=job.pk)
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "object": job,
            },
        )


class JobDetailView(LoginRequiredMixin, View):
    template_name = "jobs/detail.html"

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        
        # Security check: only owner or staff can access
        is_owner = job.created_by == request.user
        is_staff_member = job.job_staff.filter(professional=request.user).exists()
        
        if not (is_owner or is_staff_member or request.user.is_superuser):
            return redirect('jobs:list')
        
        expenses = job.expenses.filter(is_active=True)
        total_expenses = sum(e.value for e in expenses)
        net_profit = (job.cache or 0) - total_expenses
        staff = job.job_staff.all()
        
        # Agency (Business plan) can manage staff; Professionals (Pro/Free) cannot
        can_manage_staff = (is_owner and request.user.can_associate_professionals()) or request.user.is_superuser
        
        user_cache_value = None
        user_confirmed_cache = None
        show_invite_modal = False
        user_staff_record = None
        
        if is_staff_member:
            user_staff_record = staff.filter(professional=request.user).first()
            user_cache_value = user_staff_record.cache_value
            # Only show confirmed cache
            if user_staff_record.status == JobStaffStatus.CONFIRMED:
                user_confirmed_cache = user_staff_record.cache_value
            # Show invite modal if pending
            if user_staff_record.status == JobStaffStatus.PENDING:
                show_invite_modal = True
        
        available_professionals = []
        if can_manage_staff:
            current_staff_ids = staff.values_list("professional_id", flat=True)
            available_professionals = User.objects.filter(
                is_active=True,
                is_staff=False,
                plan__type__in=[PlanType.PROFESSIONAL, PlanType.FREE],
            ).exclude(pk=job.created_by.pk).exclude(pk__in=current_staff_ids)
        
        return render(
            request,
            self.template_name,
            {
                "job": job,
                "expenses": expenses,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "staff": staff,
                "is_owner": is_owner,
                "is_staff_member": is_staff_member,
                "can_manage_staff": can_manage_staff,
                "user_cache_value": user_cache_value,
                "user_confirmed_cache": user_confirmed_cache,
                "show_invite_modal": show_invite_modal,
                "user_staff_record": user_staff_record,
                "available_professionals": available_professionals,
                "professional_roles": ProfessionalRole.choices,
                "payment_types": PaymentType.choices,
            },
        )


class JobConfirmView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, created_by=request.user, is_active=True)

        if job.status == JobStatus.PENDING:
            job.status = JobStatus.CONFIRMED
            job.save()

            if job.payment_type == PaymentType.ADVANCE and job.payment_status != PaymentStatusJob.PAID:
                job.payment_status = PaymentStatusJob.PAID
                job.save()
                messages.success(request, "Trabalho confirmado! Pagamento antecipado registrado.")
            else:
                messages.success(request, "Trabalho confirmado com sucesso!")

        return redirect("jobs:detail", pk=job.pk)


class JobCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, created_by=request.user, is_active=True)
        job.status = JobStatus.COMPLETED
        job.save()
        messages.success(request, "Trabalho marcado como concluído!")
        return redirect("jobs:detail", pk=job.pk)


class JobCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, created_by=request.user, is_active=True)
        job.status = JobStatus.CANCELLED
        job.cache = 0
        job.total_budget = 0
        job.payment_total = 0
        job.payment_partial_value = 0
        job.payment_remaining_value = 0
        job.payment_status = PaymentStatusJob.PENDING
        job.save()

        job.job_staff.update(cache_value=0)

        messages.success(request, "Trabalho cancelado!")
        return redirect("jobs:list")


class JobApproveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        job.approved_by = request.user
        job.approved_at = timezone.now()
        job.save()
        messages.success(request, "Trabalho aprovado com sucesso!")
        return redirect("jobs:detail", pk=job.pk)


class JobConfirmPaymentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        if job.payment_status == PaymentStatusJob.PAID:
            messages.info(request, "Pagamento já está confirmado.")
        else:
            job.payment_status = PaymentStatusJob.PAID
            job.payment_confirmed_at = timezone.now()
            job.save()
            messages.success(request, "Pagamento confirmado com sucesso!")
        return redirect("jobs:detail", pk=job.pk)


class JobConfirmPartialPaymentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        if job.payment_type == PaymentType.PARTIAL and job.payment_status == PaymentStatusJob.PENDING:
            job.payment_status = PaymentStatusJob.PARTIAL
            job.payment_partial_confirmed_at = timezone.now()
            job.save()
            messages.success(request, "1ª parcela confirmada!")
        else:
            messages.info(request, "Não é possível confirmar 1ª parcela.")
        return redirect("jobs:detail", pk=job.pk)


class JobConfirmRemainingPaymentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, is_active=True)
        if job.payment_type == PaymentType.PARTIAL and job.payment_status in [PaymentStatusJob.PENDING, PaymentStatusJob.PARTIAL]:
            job.payment_status = PaymentStatusJob.PAID
            job.payment_remaining_confirmed_at = timezone.now()
            job.save()
            messages.success(request, "2ª parcela confirmada! Pagamento completo.")
        else:
            messages.info(request, "Não é possível confirmar 2ª parcela.")
        return redirect("jobs:detail", pk=job.pk)


class JobDeleteView(LoginRequiredMixin, View):
    template_name = "jobs/confirm_delete.html"

    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk, created_by=request.user, is_active=True)
        return render(request, self.template_name, {"job": job})

    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, created_by=request.user, is_active=True)
        job.delete()
        messages.success(request, "Trabalho excluído com sucesso!")
        return redirect("jobs:list")


class JobDuplicateView(LoginRequiredMixin, View):
    def _duplicate(self, request, pk):
        job = get_object_or_404(Job, pk=pk, is_active=True)

        is_owner = job.created_by == request.user
        if not (is_owner or request.user.is_superuser):
            messages.error(request, "Você não tem permissão para duplicar este trabalho.")
            return redirect("jobs:list")

        with transaction.atomic():
            original_pk = job.pk
            job.pk = None
            job.status = JobStatus.PENDING
            job.payment_status = PaymentStatusJob.PENDING
            job.approved_by = None
            job.approved_at = None
            job.payment_confirmed_at = None
            job.payment_partial_confirmed_at = None
            job.payment_remaining_confirmed_at = None
            job.created_by = request.user
            job.save()
            new_job = job

            original_staff = JobStaff.objects.filter(job_id=original_pk)
            for staff in original_staff:
                JobStaff.objects.create(
                    job=new_job,
                    professional=staff.professional,
                    cache_value=staff.cache_value,
                    role=staff.role,
                    payment_type=staff.payment_type,
                    status=JobStaffStatus.PENDING,
                    notes=staff.notes,
                )

            from base.expenses.models import Expense

            original_expenses = Expense.objects.filter(job_id=original_pk, is_active=True)
            for expense in original_expenses:
                Expense.objects.create(
                    performed_by=request.user,
                    job=new_job,
                    category=expense.category,
                    value=expense.value,
                    date=expense.date,
                    description=expense.description,
                    is_active=True,
                )

        messages.success(request, "Trabalho duplicado com sucesso! Revise os dados antes de confirmar.")
        return redirect("jobs:update", pk=new_job.pk)

    def post(self, request, pk):
        return self._duplicate(request, pk)

    def get(self, request, pk):
        return self._duplicate(request, pk)


class JobTeamPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        job = get_object_or_404(Job, pk=pk, is_active=True)

        is_owner = job.created_by == request.user
        if not (is_owner or request.user.is_superuser):
            return HttpResponse("Sem permissão", status=403)

        staff = job.job_staff.select_related("professional").order_by("professional__first_name", "professional__last_name")

        html = render_to_string(
            "jobs/team_list_pdf.html",
            {
                "job": job,
                "staff": staff,
                "generated_at": timezone.now(),
            },
        )

        pdf = weasyprint.HTML(string=html).write_pdf()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="equipe_{job.pk}.pdf"'
        return response


class ClientQuickCreateView(LoginRequiredMixin, View):
    template_name = "clients/quick_form.html"

    def post(self, request):
        from base.clients.forms import ClientForm

        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()
            return render(
                request, self.template_name, {"success": True, "client": client}
            )


from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()


class JobAddStaffView(LoginRequiredMixin, View):
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, created_by=request.user, is_active=True)
        
        if not request.user.can_associate_professionals() and not request.user.is_superuser:
            return JsonResponse({"success": False, "error": "Você não tem permissão para adicionar profissionais."}, status=403)
        
        professional_ids = request.POST.getlist("professionals")
        if not professional_ids:
            single_professional = request.POST.get("professional")
            if single_professional:
                professional_ids = [single_professional]
        role = request.POST.get("role")
        cache_value = request.POST.get("cache_value")
        
        if not professional_ids:
            return JsonResponse({"success": False, "error": "Selecione pelo menos um profissional."}, status=400)
        
        for pro_id in professional_ids:
            try:
                professional = User.objects.get(pk=pro_id, is_active=True, is_staff=False)
                defaults = {
                    "status": JobStaffStatus.PENDING,
                }
                # Only set cache_value if provided, otherwise leave it NULL
                if cache_value:
                    defaults["cache_value"] = float(cache_value)
                if role and role in ProfessionalRole.values:
                    defaults["role"] = role
                JobStaff.objects.update_or_create(
                    job=job,
                    professional=professional,
                    defaults=defaults
                )
            except (User.DoesNotExist, ValueError):
                pass
        
        return JsonResponse({"success": True})
        return render(request, self.template_name, {"form": form, "error": True})


class ProfessionalSearchView(LoginRequiredMixin, View):
    def get(self, request):
        from django.db.models import Q
        
        query = request.GET.get("q", "").strip()
        
        if len(query) < 2:
            return JsonResponse({"professionals": []}, safe=False)
        
        job_id = request.GET.get("job_id")
        current_staff_ids = []
        if job_id:
            current_staff_ids = list(JobStaff.objects.filter(job_id=job_id).values_list("professional_id", flat=True))
        
        professionals = User.objects.filter(
            is_active=True,
            is_staff=False,
            plan__type__in=[PlanType.PROFESSIONAL, PlanType.FREE],
        ).exclude(pk__in=current_staff_ids).filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )[:20]
        
        data = [{
            "id": pro.id,
            "name": pro.get_full_name() or pro.username,
            "phone": pro.phone or "",
            "email": pro.email or ""
        } for pro in professionals]
        
        return JsonResponse({"professionals": data}, safe=False)


class JobUpdateStaffView(LoginRequiredMixin, View):
    """Update an individual JobStaff record (role, cache_value, notes, status)"""
    def post(self, request, pk, staff_pk):
        try:
            job_staff = JobStaff.objects.get(job_id=pk, pk=staff_pk)
        except JobStaff.DoesNotExist:
            return JsonResponse({"success": False, "error": "Registro não encontrado"}, status=404)
        
        job = job_staff.job
        
        # Allow if: (1) job owner, (2) has professional association permission, (3) superuser
        is_owner = job.created_by == request.user
        has_permission = request.user.can_associate_professionals()
        if not (is_owner or has_permission or request.user.is_superuser):
            return JsonResponse({"success": False, "error": "Sem permissão"}, status=403)
        
        try:
            role = request.POST.get("role")
            cache_value = request.POST.get("cache_value")
            notes = request.POST.get("notes")
            status = request.POST.get("status")
            payment_type = request.POST.get("payment_type")
            
            # Update role if provided
            if role is not None:
                if role == '':
                    job_staff.role = None
                elif role in ProfessionalRole.values:
                    job_staff.role = role
            
            if cache_value is not None and cache_value != '':
                try:
                    job_staff.cache_value = float(cache_value)
                except (ValueError, TypeError):
                    return JsonResponse({"success": False, "error": "Valor de cache inválido"}, status=400)
            
            # Notes is optional - only update if provided (including empty string to clear it)
            if notes is not None:
                job_staff.notes = notes
            
            if status and status in JobStaffStatus.values:
                job_staff.status = status
            
            # Update payment_type if provided
            if payment_type is not None:
                if payment_type == '':
                    job_staff.payment_type = None
                elif payment_type in PaymentType.values:
                    job_staff.payment_type = payment_type
            
            job_staff.save()
            return JsonResponse({"success": True})
        except Exception as e:
            import traceback
            print(f"Error in JobUpdateStaffView: {e}")
            print(traceback.format_exc())
            return JsonResponse({"success": False, "error": str(e)}, status=500)


class JobRemoveStaffView(LoginRequiredMixin, View):
    """Remove a professional from the job staff"""
    def post(self, request, pk, staff_pk):
        try:
            job_staff = JobStaff.objects.get(job_id=pk, pk=staff_pk)
        except JobStaff.DoesNotExist:
            return JsonResponse({"success": False, "error": "Registro não encontrado"}, status=404)
        
        job = job_staff.job
        
        # Allow if: (1) job owner, (2) has professional association permission, (3) superuser
        is_owner = job.created_by == request.user
        has_permission = request.user.can_associate_professionals()
        if not (is_owner or has_permission or request.user.is_superuser):
            return JsonResponse({"success": False, "error": "Sem permissão"}, status=403)
        
        job_staff.delete()
        return JsonResponse({"success": True})


class JobStaffStatusUpdateView(LoginRequiredMixin, View):
    """Allow staff members to update their own status (accept/confirm/cancel/paid)"""
    def post(self, request, pk, staff_pk):
        try:
            job_staff = JobStaff.objects.get(
                job_id=pk, 
                pk=staff_pk, 
                professional=request.user
            )
        except JobStaff.DoesNotExist:
            return JsonResponse({"success": False, "error": "Registro não encontrado"}, status=404)
        
        current_status = job_staff.status
        new_status = request.POST.get("status")
        
        if not new_status or new_status not in JobStaffStatus.values:
            return JsonResponse({"success": False, "error": "Status inválido"}, status=400)
        
        # Handle rejection/cancellation - delete record (professional no longer participates)
        if new_status in [JobStaffStatus.REJECTED, JobStaffStatus.CANCELLED_BY_PROF]:
            job_staff.delete()
            return JsonResponse({"success": True, "redirect": True})
        
        # Validate status transitions
        if new_status == JobStaffStatus.ACCEPTED and current_status != JobStaffStatus.PENDING:
            return JsonResponse({"success": False, "error": "Só pode aceitar convites pendentes"}, status=400)
        
        if new_status == JobStaffStatus.CONFIRMED and current_status not in [JobStaffStatus.PENDING, JobStaffStatus.ACCEPTED]:
            return JsonResponse({"success": False, "error": "Só pode confirmar presença de convites aceitos ou pendentes"}, status=400)
        
        if new_status == JobStaffStatus.CANCELLED_BY_PROF and current_status not in [JobStaffStatus.PENDING, JobStaffStatus.ACCEPTED, JobStaffStatus.CONFIRMED]:
            return JsonResponse({"success": False, "error": "Só pode cancelar se estiver pendente, aceito ou confirmado"}, status=400)
        
        if new_status == JobStaffStatus.PAID and current_status != JobStaffStatus.CONFIRMED:
            return JsonResponse({"success": False, "error": "Só pode marcar como pago após confirmação de presença"}, status=400)
        
        job_staff.status = new_status
        job_staff.save()
        return JsonResponse({"success": True})
