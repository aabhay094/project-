from .models import StaticPage


def footer_pages(request):
    """Injects published, footer-visible StaticPage links into every template."""
    pages = StaticPage.objects.filter(is_published=True, show_in_footer=True).order_by("title")
    return {"footer_pages": pages}
