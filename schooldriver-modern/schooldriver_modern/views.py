from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.db import connection
from .roles import get_user_role, UserRoles
import json


@staff_member_required
def dashboard_view(request):
    """Dashboard view with 4 interactive charts for admission analytics."""

    # Admission pipeline progress (funnel chart)
    pipeline_data = {
        "labels": ["Applied", "Reviewed", "Interviewed", "Accepted"],
        "values": [1200, 800, 450, 280],
        "colors": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
    }

    # Document completion rates (bar chart)
    documents_data = {
        "labels": [
            "Transcripts",
            "Letters of Rec",
            "Personal Statement",
            "Test Scores",
            "Application Form",
        ],
        "completion_rates": [95, 87, 92, 78, 98],
        "colors": ["#6366F1", "#8B5CF6", "#EC4899", "#F97316", "#84CC16"],
    }

    # Applicant status distribution (pie chart)
    status_data = {
        "labels": [
            "Pending Review",
            "Under Consideration",
            "Interviewed",
            "Accepted",
            "Waitlisted",
            "Declined",
        ],
        "values": [320, 280, 150, 180, 95, 175],
        "colors": ["#64748B", "#3B82F6", "#10B981", "#22C55E", "#F59E0B", "#EF4444"],
    }

    # Monthly admission trends (line chart)
    trends_data = {
        "labels": [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        "applications": [45, 62, 78, 95, 120, 110, 85, 92, 145, 168, 142, 98],
        "acceptances": [12, 18, 25, 32, 41, 38, 28, 31, 52, 58, 48, 35],
    }

    # Combine all chart data
    dashboard_data = {
        "pipeline": pipeline_data,
        "documents": documents_data,
        "status": status_data,
        "trends": trends_data,
        "summary": {
            "total_applications": sum(trends_data["applications"]),
            "total_acceptances": sum(trends_data["acceptances"]),
            "acceptance_rate": round(
                sum(trends_data["acceptances"])
                / sum(trends_data["applications"])
                * 100,
                1,
            ),
            "pending_applications": status_data["values"][0] + status_data["values"][1],
        },
    }

    context = {
        "dashboard_data": dashboard_data,
        "dashboard_data_json": json.dumps(dashboard_data),
    }

    return render(request, "dashboard.html", context)


@login_required
def parent_view(request):
    """Parent portal view - restricted to parents."""
    user_role = get_user_role(request.user)

    if user_role != UserRoles.PARENT:
        return HttpResponseForbidden("Access restricted to parents only.")

    context = {
        "user_role": user_role,
        "children": [
            {"name": "Alice Johnson", "grade": "5th Grade", "teacher": "Mrs. Smith"},
            {"name": "Bob Johnson", "grade": "3rd Grade", "teacher": "Mr. Brown"},
        ],  # Dummy data for demonstration
    }

    return render(request, "parent_portal.html", context)


@login_required
def student_view(request):
    """Student portal view - restricted to students."""
    user_role = get_user_role(request.user)

    if user_role != UserRoles.STUDENT:
        return HttpResponseForbidden("Access restricted to students only.")

    context = {
        "user_role": user_role,
        "courses": [
            {"name": "Mathematics", "teacher": "Mrs. Wilson", "grade": "A-"},
            {"name": "English Literature", "teacher": "Mr. Davis", "grade": "B+"},
            {"name": "Biology", "teacher": "Dr. Martinez", "grade": "A"},
        ],  # Dummy data for demonstration
        "assignments": [
            {"title": "Math Homework #5", "due_date": "Tomorrow", "status": "Pending"},
            {"title": "English Essay", "due_date": "Friday", "status": "Submitted"},
        ],
    }

    return render(request, "student_portal.html", context)


@staff_member_required
def admin_dashboard_view(request):
    """Admin-style dashboard view matching the main admin interface."""

    # Admission pipeline progress (funnel chart)
    pipeline_data = {
        "labels": ["Applied", "Reviewed", "Interviewed", "Accepted"],
        "values": [1200, 800, 450, 280],
        "colors": ["#3B82F6", "#10B981", "#F59E0B", "#EF4444"],
    }

    # Document completion rates (bar chart)
    documents_data = {
        "labels": [
            "Transcripts",
            "Letters of Rec",
            "Personal Statement",
            "Test Scores",
            "Application Form",
        ],
        "completion_rates": [95, 87, 92, 78, 98],
        "colors": ["#6366F1", "#8B5CF6", "#EC4899", "#F97316", "#84CC16"],
    }

    # Applicant status distribution (pie chart)
    status_data = {
        "labels": [
            "Pending Review",
            "Under Consideration",
            "Interviewed",
            "Accepted",
            "Waitlisted",
            "Declined",
        ],
        "values": [320, 280, 150, 180, 95, 175],
        "colors": ["#64748B", "#3B82F6", "#10B981", "#22C55E", "#F59E0B", "#EF4444"],
    }

    # Monthly admission trends (line chart)
    trends_data = {
        "labels": [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ],
        "applications": [45, 62, 78, 95, 120, 110, 85, 92, 145, 168, 142, 98],
        "acceptances": [12, 18, 25, 32, 41, 38, 28, 31, 52, 58, 48, 35],
    }

    # Combine all chart data
    dashboard_data = {
        "pipeline": pipeline_data,
        "documents": documents_data,
        "status": status_data,
        "trends": trends_data,
        "summary": {
            "total_applications": sum(trends_data["applications"]),
            "total_acceptances": sum(trends_data["acceptances"]),
            "acceptance_rate": round(
                sum(trends_data["acceptances"])
                / sum(trends_data["applications"])
                * 100,
                1,
            ),
            "pending_applications": status_data["values"][0] + status_data["values"][1],
        },
    }

    context = {
        "dashboard_data": dashboard_data,
        "dashboard_data_json": json.dumps(dashboard_data),
    }

    return render(request, "admin_dashboard.html", context)


def health_check(request):
    """Health check endpoint for monitoring and Docker health checks."""
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return JsonResponse(
            {
                "status": "healthy",
                "database": "connected",
                "timestamp": json.dumps(None),  # Will be set by client
            }
        )
    except Exception as e:
        return JsonResponse({"status": "unhealthy", "error": str(e)}, status=500)
