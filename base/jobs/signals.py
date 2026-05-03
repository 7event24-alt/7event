from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import JobStaff, JobStaffStatus
from base.accounts.models import Notification, NotificationType
from base.accounts.api_urls import send_push_notification


@receiver(post_save, sender=JobStaff)
def notify_professional_on_staff_add(sender, instance, created, **kwargs):
    """Send notification to professional when added to a job team"""
    if created:  # Only on creation
        try:
            # Create in-app notification
            Notification.objects.create(
                user=instance.professional,
                title="Novo convite de trabalho",
                message=f"Você foi adicionado ao trabalho '{instance.job.title}'",
                action_url=f"/app/trabalhos/{instance.job.pk}/",
                notification_type=NotificationType.JOB,
            )
            
            # Send push notification
            send_push_notification(
                user=instance.professional,
                title="Novo convite de trabalho",
                body=f"Você foi adicionado ao trabalho '{instance.job.title}'",
                action_url=f"/app/trabalhos/{instance.job.pk}/"
            )
        except Exception as e:
            print(f"Error sending notification to professional: {e}")


@receiver(post_save, sender=JobStaff)
def notify_owner_on_status_change(sender, instance, created, **kwargs):
    """Send notification to job owner when staff accepts/recuses"""
    if not created and instance.status in [JobStaffStatus.ACCEPTED, JobStaffStatus.REJECTED]:
        try:
            status_text = "aceitou" if instance.status == JobStaffStatus.ACCEPTED else "recusou"
            Notification.objects.create(
                user=instance.job.created_by,
                title="Atualização na equipe",
                message=f"{instance.professional.get_full_name() or instance.professional.username} {status_text} o convite para '{instance.job.title}'",
                action_url=f"/app/trabalhos/{instance.job.pk}/",
                notification_type=NotificationType.JOB,
            )
        except Exception as e:
            print(f"Error sending notification to owner: {e}")
