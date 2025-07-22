"""
Role-Based Access Control (RBAC) system for SchoolDriver Modern.

Defines user roles and provides utilities for role management.
"""

from django.contrib.auth.models import Group, User
import logging

logger = logging.getLogger(__name__)


# Define available roles
class UserRoles:
    """Constants for user roles in the system."""

    ADMIN = "Admin"
    STAFF = "Staff"
    PARENT = "Parent"
    STUDENT = "Student"

    ALL_ROLES = [ADMIN, STAFF, PARENT, STUDENT]

    # Role descriptions
    DESCRIPTIONS = {
        ADMIN: "System administrators with full access",
        STAFF: "School staff with dashboard access",
        PARENT: "Parents with access to their children's information",
        STUDENT: "Students with access to their own information",
    }

    # Default redirect URLs for each role
    REDIRECT_URLS = {
        ADMIN: "/admin/",
        STAFF: "/dashboard/",
        PARENT: "/parent/",
        STUDENT: "/student/",
    }


def create_default_groups():
    """Create default permission groups for all user roles."""
    created_groups = []

    for role in UserRoles.ALL_ROLES:
        group, created = Group.objects.get_or_create(name=role)
        if created:
            created_groups.append(role)
            logger.info(f"Created group: {role}")
        else:
            logger.debug(f"Group already exists: {role}")

    return created_groups


def get_user_role(user):
    """
    Get the primary role of a user based on their group membership.

    Priority order: Admin > Staff > Parent > Student

    Args:
        user: Django User instance

    Returns:
        str: Role name or None if no role assigned
    """
    if not user.is_authenticated:
        return None

    user_groups = list(user.groups.values_list("name", flat=True))

    # Check roles in priority order
    for role in UserRoles.ALL_ROLES:
        if role in user_groups:
            return role

    # Fallback: Check Django's built-in attributes
    if user.is_superuser:
        return UserRoles.ADMIN
    elif user.is_staff:
        return UserRoles.STAFF

    return None


def get_redirect_url_for_user(user):
    """
    Get the appropriate redirect URL for a user based on their role.

    Args:
        user: Django User instance

    Returns:
        str: URL to redirect to
    """
    role = get_user_role(user)
    return UserRoles.REDIRECT_URLS.get(role, "/dashboard/")


def assign_role_to_user(user, role):
    """
    Assign a role (group) to a user.

    Args:
        user: Django User instance
        role: Role name from UserRoles

    Returns:
        bool: True if role was assigned successfully
    """
    if role not in UserRoles.ALL_ROLES:
        logger.error(f"Invalid role: {role}")
        return False

    try:
        group = Group.objects.get(name=role)
        user.groups.add(group)
        logger.info(f"Assigned role {role} to user {user.username}")
        return True
    except Group.DoesNotExist:
        logger.error(f"Group {role} does not exist")
        return False


def remove_role_from_user(user, role):
    """
    Remove a role (group) from a user.

    Args:
        user: Django User instance
        role: Role name from UserRoles

    Returns:
        bool: True if role was removed successfully
    """
    if role not in UserRoles.ALL_ROLES:
        logger.error(f"Invalid role: {role}")
        return False

    try:
        group = Group.objects.get(name=role)
        user.groups.remove(group)
        logger.info(f"Removed role {role} from user {user.username}")
        return True
    except Group.DoesNotExist:
        logger.error(f"Group {role} does not exist")
        return False


def get_users_by_role(role):
    """
    Get all users with a specific role.

    Args:
        role: Role name from UserRoles

    Returns:
        QuerySet: Users with the specified role
    """
    if role not in UserRoles.ALL_ROLES:
        return User.objects.none()

    try:
        group = Group.objects.get(name=role)
        return group.user_set.all()
    except Group.DoesNotExist:
        return User.objects.none()
