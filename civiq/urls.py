from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("lodge/", views.lodge_complaint, name="lodge_complaint"),
    path("lodge/nlp-preview/", views.nlp_preview, name="nlp_preview"),
    path("track/", views.track_complaint, name="track_complaint"),
    path("departments/", views.departments, name="departments"),
    path("analytics/", views.analytics, name="analytics"),
    path("team/", views.team, name="team"),
    path("page/<slug:slug>/", views.page_detail, name="page_detail"),

    # Officer workspace
    path("officer/login/", auth_views.LoginView.as_view(template_name="officer_login.html"), name="officer_login"),
    path("officer/logout/", auth_views.LogoutView.as_view(next_page="home"), name="officer_logout"),
    path("officer/dashboard/", views.officer_dashboard, name="officer_dashboard"),
    path(
        "officer/complaint/<str:tracking_id>/update/",
        views.update_complaint_status,
        name="update_complaint_status",
    ),
]
