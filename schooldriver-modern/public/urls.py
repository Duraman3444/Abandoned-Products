from django.urls import path
from . import views

app_name = "public"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("admissions/", views.admissions_view, name="admissions"),
    path("contact/", views.contact_view, name="contact"),
    path("programs/", views.programs_view, name="programs"),
]
