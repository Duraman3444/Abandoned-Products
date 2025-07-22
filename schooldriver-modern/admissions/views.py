import csv
from django.shortcuts import render
from django.http import HttpResponse
from .models import Applicant


def applicant_csv_export(request):
    """Return a CSV of the current admissions data."""
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="admissions_analytics.csv"'},
    )
    writer = csv.writer(response)
    writer.writerow(["Applicant ID", "Status", "Applied Date", "Decision", "Acceptance Rate"])
    qs = Applicant.objects.select_related("level").all()
    for a in qs:
        writer.writerow([
            a.applicant_id or a.id,
            a.level.name if a.level else "N/A",
            a.created_at.date(),
            a.get_decision_display() if hasattr(a, "get_decision_display") else "—",
            a.get_completion_percentage() if hasattr(a, "get_completion_percentage") else "—",
        ])
    return response


# Create your views here.
