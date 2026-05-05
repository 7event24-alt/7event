from django.contrib.auth.views import PasswordResetView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy


class CustomPasswordResetView(PasswordResetView):
    email_template_name = "emails/password_reset.txt"
    html_email_template_name = "emails/password_reset.html"
    subject_template_name = "emails/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")

    def form_valid(self, form):
        request = self.request
        form.save(
            request=request,
            use_https=request.is_secure(),
            email_template_name=self.email_template_name,
            html_email_template_name=self.html_email_template_name,
            subject_template_name=self.subject_template_name,
            from_email=self.from_email,
            extra_email_context={
                "domain": request.get_host(),
                "site_name": "7event",
                "protocol": "https" if request.is_secure() else "http",
            },
        )
        return HttpResponseRedirect(self.get_success_url())
