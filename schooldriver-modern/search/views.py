from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib.auth.models import User

from students.models import Student, SchoolYear
from academics.models import Course, Assignment
from .models import SearchHistory, SavedSearch, SearchSuggestion

import json
import logging

logger = logging.getLogger(__name__)


@login_required
def global_search_view(request):
    """Global search across students, courses, teachers, and academic records."""
    query = request.GET.get("q", "").strip()
    search_type = request.GET.get("type", "all")
    filters = {
        "grade_level": request.GET.get("grade_level", ""),
        "school_year": request.GET.get("school_year", ""),
        "subject": request.GET.get("subject", ""),
        "status": request.GET.get("status", ""),
    }

    results = {
        "students": [],
        "courses": [],
        "teachers": [],
        "assignments": [],
        "total_count": 0,
    }

    if query:
        # Log search for history and suggestions
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            search_type=search_type,
            filters_applied=filters,
        )
        SearchSuggestion.increment_count(query)

        if search_type in ["all", "students"]:
            students = search_students(query, filters)
            results["students"] = students[:10]  # Limit to top 10

        if search_type in ["all", "courses"]:
            courses = search_courses(query, filters)
            results["courses"] = courses[:10]

        if search_type in ["all", "teachers"]:
            teachers = search_teachers(query, filters)
            results["teachers"] = teachers[:10]

        if search_type in ["all", "assignments"]:
            assignments = search_assignments(query, filters)
            results["assignments"] = assignments[:10]

        results["total_count"] = (
            len(results["students"])
            + len(results["courses"])
            + len(results["teachers"])
            + len(results["assignments"])
        )

        # Update search history with results count
        SearchHistory.objects.filter(user=request.user, query=query).update(
            results_count=results["total_count"]
        )

    # Get filter options
    grade_levels = Student.objects.values_list(
        "grade_level__name", flat=True
    ).distinct()
    school_years = SchoolYear.objects.values_list("name", "id").order_by("-start_date")
    subjects = Course.objects.values_list("subject", flat=True).distinct()

    # Get recent searches and saved searches
    recent_searches = SearchHistory.objects.filter(user=request.user)[:5]
    saved_searches = SavedSearch.objects.filter(user=request.user)[:5]

    context = {
        "query": query,
        "search_type": search_type,
        "filters": filters,
        "results": results,
        "grade_levels": grade_levels,
        "school_years": school_years,
        "subjects": subjects,
        "recent_searches": recent_searches,
        "saved_searches": saved_searches,
    }

    return render(request, "search/global_search.html", context)


def search_students(query, filters):
    """Search for students with filters."""
    students_query = Student.objects.select_related("grade_level")

    # Text search
    if query:
        students_query = students_query.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(student_id__icontains=query)
            | Q(primary_contact_email__icontains=query)
        )

    # Apply filters
    if filters.get("grade_level"):
        students_query = students_query.filter(grade_level__name=filters["grade_level"])

    if filters.get("status"):
        is_active = filters["status"] == "active"
        students_query = students_query.filter(is_active=is_active)

    return [
        {
            "id": student.id,
            "name": f"{student.first_name} {student.last_name}",
            "student_id": student.student_id,
            "grade_level": student.grade_level.name if student.grade_level else "N/A",
            "email": student.primary_contact_email,
            "is_active": student.is_active,
        }
        for student in students_query[:50]
    ]


def search_courses(query, filters):
    """Search for courses with filters."""
    courses_query = Course.objects.all()

    # Text search
    if query:
        courses_query = courses_query.filter(
            Q(name__icontains=query)
            | Q(subject__icontains=query)
            | Q(description__icontains=query)
        )

    # Apply filters
    if filters.get("subject"):
        courses_query = courses_query.filter(subject=filters["subject"])

    if filters.get("school_year"):
        courses_query = courses_query.filter(
            sections__school_year_id=filters["school_year"]
        ).distinct()

    return [
        {
            "id": course.id,
            "name": course.name,
            "subject": course.subject,
            "credit_hours": course.credit_hours,
            "description": course.description[:100] + "..."
            if course.description and len(course.description) > 100
            else course.description,
        }
        for course in courses_query[:50]
    ]


def search_teachers(query, filters):
    """Search for teachers (users with teacher role)."""
    # For now, we'll search all users - in production you'd filter by role
    teachers_query = User.objects.filter(is_active=True)

    # Text search
    if query:
        teachers_query = teachers_query.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(username__icontains=query)
        )

    # Filter teachers who actually teach courses
    if filters.get("subject"):
        teachers_query = teachers_query.filter(
            taught_sections__course__subject=filters["subject"]
        ).distinct()

    if filters.get("school_year"):
        teachers_query = teachers_query.filter(
            taught_sections__school_year_id=filters["school_year"]
        ).distinct()

    return [
        {
            "id": teacher.id,
            "name": f"{teacher.first_name} {teacher.last_name}",
            "email": teacher.email,
            "username": teacher.username,
            "courses_count": teacher.taught_sections.count()
            if hasattr(teacher, "taught_sections")
            else 0,
        }
        for teacher in teachers_query[:50]
    ]


def search_assignments(query, filters):
    """Search for assignments with filters."""
    assignments_query = Assignment.objects.select_related("section__course")

    # Text search
    if query:
        assignments_query = assignments_query.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(section__course__name__icontains=query)
        )

    # Apply filters
    if filters.get("subject"):
        assignments_query = assignments_query.filter(
            section__course__subject=filters["subject"]
        )

    if filters.get("school_year"):
        assignments_query = assignments_query.filter(
            section__school_year_id=filters["school_year"]
        )

    return [
        {
            "id": assignment.id,
            "name": assignment.name,
            "course": assignment.section.course.name,
            "due_date": assignment.due_date,
            "max_points": assignment.max_points,
            "is_published": assignment.is_published,
        }
        for assignment in assignments_query[:50]
    ]


@login_required
@require_http_methods(["GET"])
def search_suggestions_api(request):
    """API endpoint for search suggestions."""
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "general")

    if not query or len(query) < 2:
        return JsonResponse({"suggestions": []})

    # Get suggestions from SearchSuggestion model
    suggestions = SearchSuggestion.objects.filter(term__icontains=query).order_by(
        "-search_count"
    )[:10]

    # Also get live suggestions from models
    live_suggestions = []

    # Student names
    if category in ["general", "student_name"]:
        students = Student.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )[:5]
        live_suggestions.extend([f"{s.first_name} {s.last_name}" for s in students])

    # Course names
    if category in ["general", "course_name"]:
        courses = Course.objects.filter(name__icontains=query)[:5]
        live_suggestions.extend([c.name for c in courses])

    # Teacher names
    if category in ["general", "teacher_name"]:
        teachers = User.objects.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query),
            is_active=True,
        )[:5]
        live_suggestions.extend(
            [
                f"{t.first_name} {t.last_name}"
                for t in teachers
                if t.first_name and t.last_name
            ]
        )

    # Combine and deduplicate
    all_suggestions = []
    seen = set()

    # Prioritize stored suggestions
    for suggestion in suggestions:
        if suggestion.term not in seen:
            all_suggestions.append(
                {
                    "text": suggestion.term,
                    "category": suggestion.category,
                    "count": suggestion.search_count,
                }
            )
            seen.add(suggestion.term)

    # Add live suggestions
    for suggestion in live_suggestions:
        if suggestion not in seen and len(all_suggestions) < 10:
            all_suggestions.append(
                {"text": suggestion, "category": category, "count": 0}
            )
            seen.add(suggestion)

    return JsonResponse({"suggestions": all_suggestions})


@login_required
@require_http_methods(["POST"])
def save_search(request):
    """Save a search for later use."""
    try:
        data = json.loads(request.body)
        name = data.get("name", "").strip()
        query = data.get("query", "").strip()
        search_type = data.get("search_type", "global")
        filters = data.get("filters", {})

        if not name or not query:
            return JsonResponse({"error": "Name and query are required"}, status=400)

        saved_search, created = SavedSearch.objects.get_or_create(
            user=request.user,
            name=name,
            defaults={"query": query, "search_type": search_type, "filters": filters},
        )

        if not created:
            # Update existing saved search
            saved_search.query = query
            saved_search.search_type = search_type
            saved_search.filters = filters
            saved_search.save()

        return JsonResponse(
            {"success": True, "message": f'Search "{name}" saved successfully'}
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Error saving search: {e}")
        return JsonResponse({"error": "Failed to save search"}, status=500)


@login_required
@require_http_methods(["DELETE"])
def delete_saved_search(request, search_id):
    """Delete a saved search."""
    try:
        saved_search = SavedSearch.objects.get(id=search_id, user=request.user)
        name = saved_search.name
        saved_search.delete()
        return JsonResponse(
            {"success": True, "message": f'Search "{name}" deleted successfully'}
        )
    except SavedSearch.DoesNotExist:
        return JsonResponse({"error": "Saved search not found"}, status=404)
    except Exception as e:
        logger.error(f"Error deleting saved search: {e}")
        return JsonResponse({"error": "Failed to delete search"}, status=500)


@login_required
def load_saved_search(request, search_id):
    """Load a saved search and redirect to search page."""
    try:
        saved_search = SavedSearch.objects.get(id=search_id, user=request.user)

        # Update last_used timestamp
        saved_search.last_used = timezone.now()
        saved_search.save()

        # Build query parameters
        params = {
            "q": saved_search.query,
            "type": saved_search.search_type,
        }
        params.update(saved_search.filters)

        # Build query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items() if v])

        return redirect(f"/search/?{query_string}")

    except SavedSearch.DoesNotExist:
        messages.error(request, "Saved search not found.")
        return redirect("search:global_search")
