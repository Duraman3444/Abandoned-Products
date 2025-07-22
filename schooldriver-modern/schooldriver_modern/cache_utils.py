"""
Caching utilities for SchoolDriver Modern.
"""

from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Cache timeouts (in seconds)
DEFAULT_TIMEOUT = 60 * 15  # 15 minutes
SHORT_TIMEOUT = 60 * 5  # 5 minutes
LONG_TIMEOUT = 60 * 60  # 1 hour
DAILY_TIMEOUT = 60 * 60 * 24  # 24 hours

# Cache key prefixes
STUDENT_DATA_PREFIX = "student_data"
ENROLLMENT_PREFIX = "enrollment"
SCHOOL_YEAR_PREFIX = "school_year"
DASHBOARD_PREFIX = "dashboard"
ANNOUNCEMENTS_PREFIX = "announcements"


def get_cache_key(*parts):
    """
    Generate a cache key from parts.

    Args:
        *parts: Parts to join for the cache key

    Returns:
        str: Cache key
    """
    return ":".join(str(part) for part in parts)


def cache_student_enrollments(student_id, school_year_id=None):
    """
    Cache student enrollments for a school year.

    Args:
        student_id: Student ID
        school_year_id: School year ID (optional)

    Returns:
        str: Cache key used
    """
    from academics.models import Enrollment
    from students.models import SchoolYear

    if not school_year_id:
        school_year = SchoolYear.objects.filter(is_active=True).first()
        school_year_id = school_year.id if school_year else None

    if not school_year_id:
        return None

    cache_key = get_cache_key(ENROLLMENT_PREFIX, student_id, school_year_id)

    try:
        enrollments = list(
            Enrollment.objects.filter(
                student_id=student_id,
                section__school_year_id=school_year_id,
                is_active=True,
            )
            .select_related(
                "section__course__department",
                "section__teacher",
                "section__school_year",
            )
            .values(
                "id",
                "section__course__name",
                "section__course__course_code",
                "section__course__credit_hours",
                "section__teacher__first_name",
                "section__teacher__last_name",
                "section__room",
                "section_id",
            )
        )

        cache.set(cache_key, enrollments, DEFAULT_TIMEOUT)
        logger.debug(f"Cached enrollments for student {student_id}: {cache_key}")

    except Exception as e:
        logger.error(f"Error caching student enrollments: {e}")

    return cache_key


def get_cached_student_enrollments(student_id, school_year_id=None):
    """
    Get cached student enrollments.

    Args:
        student_id: Student ID
        school_year_id: School year ID (optional)

    Returns:
        list: Cached enrollments or None if not cached
    """
    from students.models import SchoolYear

    if not school_year_id:
        school_year = SchoolYear.objects.filter(is_active=True).first()
        school_year_id = school_year.id if school_year else None

    if not school_year_id:
        return None

    cache_key = get_cache_key(ENROLLMENT_PREFIX, student_id, school_year_id)
    return cache.get(cache_key)


def cache_active_school_year():
    """
    Cache the active school year.

    Returns:
        str: Cache key used
    """
    from students.models import SchoolYear

    cache_key = get_cache_key(SCHOOL_YEAR_PREFIX, "active")

    try:
        school_year = SchoolYear.objects.filter(is_active=True).first()
        if school_year:
            school_year_data = {
                "id": str(school_year.id),
                "name": school_year.name,
                "start_date": school_year.start_date.isoformat(),
                "end_date": school_year.end_date.isoformat(),
                "is_active": school_year.is_active,
            }
            cache.set(cache_key, school_year_data, LONG_TIMEOUT)
            logger.debug(f"Cached active school year: {cache_key}")

    except Exception as e:
        logger.error(f"Error caching active school year: {e}")

    return cache_key


def get_cached_active_school_year():
    """
    Get cached active school year.

    Returns:
        dict: Cached school year data or None if not cached
    """
    cache_key = get_cache_key(SCHOOL_YEAR_PREFIX, "active")
    return cache.get(cache_key)


def cache_student_dashboard_data(student_id):
    """
    Cache student dashboard data.

    Args:
        student_id: Student ID

    Returns:
        str: Cache key used
    """
    cache_key = get_cache_key(DASHBOARD_PREFIX, student_id)

    try:
        # Import here to avoid circular imports
        from student_portal.views import get_student_academic_data
        from students.models import Student

        student = Student.objects.get(id=student_id)
        dashboard_data = get_student_academic_data(student)

        # Convert to serializable format
        serializable_data = {
            "current_courses": dashboard_data.get("current_courses", []),
            "gpa": float(dashboard_data.get("gpa", 0.0)),
            "gpa_letter": dashboard_data.get("gpa_letter", "N/A"),
            "credit_hours_total": float(dashboard_data.get("credit_hours_total", 0.0)),
            "attendance_percentage": float(
                dashboard_data.get("attendance_percentage", 0.0)
            ),
            "cached_at": timezone.now().isoformat(),
        }

        cache.set(cache_key, serializable_data, SHORT_TIMEOUT)
        logger.debug(f"Cached dashboard data for student {student_id}: {cache_key}")

    except Exception as e:
        logger.error(f"Error caching student dashboard data: {e}")

    return cache_key


def get_cached_student_dashboard_data(student_id):
    """
    Get cached student dashboard data.

    Args:
        student_id: Student ID

    Returns:
        dict: Cached dashboard data or None if not cached
    """
    cache_key = get_cache_key(DASHBOARD_PREFIX, student_id)
    return cache.get(cache_key)


def cache_published_announcements(audience="STUDENTS"):
    """
    Cache published announcements for a specific audience.

    Args:
        audience: Announcement audience (STUDENTS, PARENTS, TEACHERS, ALL)

    Returns:
        str: Cache key used
    """
    from academics.models import Announcement

    cache_key = get_cache_key(ANNOUNCEMENTS_PREFIX, audience.lower())

    try:
        announcements = list(
            Announcement.objects.filter(
                is_published=True,
                audience__in=[audience, "ALL"],
                publish_date__lte=timezone.now(),
            )
            .select_related("created_by")
            .order_by("-publish_date")[:10]
            .values(
                "id",
                "title",
                "content",
                "audience",
                "publish_date",
                "created_by__first_name",
                "created_by__last_name",
            )
        )

        cache.set(cache_key, announcements, DEFAULT_TIMEOUT)
        logger.debug(f"Cached announcements for {audience}: {cache_key}")

    except Exception as e:
        logger.error(f"Error caching announcements: {e}")

    return cache_key


def get_cached_published_announcements(audience="STUDENTS"):
    """
    Get cached published announcements.

    Args:
        audience: Announcement audience

    Returns:
        list: Cached announcements or None if not cached
    """
    cache_key = get_cache_key(ANNOUNCEMENTS_PREFIX, audience.lower())
    return cache.get(cache_key)


def invalidate_student_cache(student_id):
    """
    Invalidate all cached data for a specific student.

    Args:
        student_id: Student ID to invalidate cache for
    """
    from students.models import SchoolYear

    # Get current school year
    school_year = SchoolYear.objects.filter(is_active=True).first()
    school_year_id = school_year.id if school_year else None

    cache_keys_to_delete = [
        get_cache_key(DASHBOARD_PREFIX, student_id),
        get_cache_key(STUDENT_DATA_PREFIX, student_id),
    ]

    if school_year_id:
        cache_keys_to_delete.append(
            get_cache_key(ENROLLMENT_PREFIX, student_id, school_year_id)
        )

    for cache_key in cache_keys_to_delete:
        cache.delete(cache_key)
        logger.debug(f"Invalidated cache key: {cache_key}")


def invalidate_school_year_cache():
    """
    Invalidate school year related cache.
    """
    cache_key = get_cache_key(SCHOOL_YEAR_PREFIX, "active")
    cache.delete(cache_key)
    logger.debug(f"Invalidated school year cache: {cache_key}")


def invalidate_announcements_cache():
    """
    Invalidate announcements cache for all audiences.
    """
    audiences = ["students", "parents", "teachers", "all"]
    for audience in audiences:
        cache_key = get_cache_key(ANNOUNCEMENTS_PREFIX, audience)
        cache.delete(cache_key)
        logger.debug(f"Invalidated announcements cache: {cache_key}")


def warm_cache_for_student(student_id):
    """
    Pre-warm cache for a student with commonly accessed data.

    Args:
        student_id: Student ID
    """
    try:
        # Warm enrollment cache
        cache_student_enrollments(student_id)

        # Warm dashboard cache
        cache_student_dashboard_data(student_id)

        # Warm announcements cache
        cache_published_announcements("STUDENTS")

        logger.info(f"Cache warmed for student {student_id}")

    except Exception as e:
        logger.error(f"Error warming cache for student {student_id}: {e}")


# Cache warming for common data
def warm_common_cache():
    """
    Pre-warm cache for commonly accessed data.
    """
    try:
        # Cache active school year
        cache_active_school_year()

        # Cache announcements for all audiences
        for audience in ["STUDENTS", "PARENTS", "TEACHERS"]:
            cache_published_announcements(audience)

        logger.info("Common cache warmed successfully")

    except Exception as e:
        logger.error(f"Error warming common cache: {e}")
