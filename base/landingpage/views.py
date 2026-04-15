from django.views.generic import TemplateView


class LandingPageView(TemplateView):
    template_name = "landingpage/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hide_nav"] = True
        return context


landing_page = LandingPageView.as_view()
