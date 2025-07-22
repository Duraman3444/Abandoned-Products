from django.urls import path
from . import views

urlpatterns = [
    path("export/csv/", views.applicant_csv_export, name="dashboard_csv_export"),
]
