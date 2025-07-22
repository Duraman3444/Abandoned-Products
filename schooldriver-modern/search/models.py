from django.db import models
from django.contrib.auth.models import User


class SearchHistory(models.Model):
    """Track user search history for suggestions and analytics."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="search_history"
    )
    query = models.CharField(max_length=255)
    search_type = models.CharField(
        max_length=50,
        choices=[
            ("global", "Global Search"),
            ("students", "Students"),
            ("courses", "Courses"),
            ("teachers", "Teachers"),
            ("grades", "Grades"),
            ("assignments", "Assignments"),
        ],
        default="global",
    )
    filters_applied = models.JSONField(default=dict, blank=True)
    results_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Search histories"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["query"]),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.query}"


class SavedSearch(models.Model):
    """Allow users to save frequently used searches."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_searches"
    )
    name = models.CharField(max_length=100)
    query = models.CharField(max_length=255)
    search_type = models.CharField(
        max_length=50,
        choices=[
            ("global", "Global Search"),
            ("students", "Students"),
            ("courses", "Courses"),
            ("teachers", "Teachers"),
            ("grades", "Grades"),
            ("assignments", "Assignments"),
        ],
        default="global",
    )
    filters = models.JSONField(default=dict, blank=True)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["user", "name"]
        ordering = ["-last_used"]

    def __str__(self):
        return f"{self.user.username}: {self.name}"


class SearchSuggestion(models.Model):
    """Popular search terms for autocomplete suggestions."""

    term = models.CharField(max_length=255, unique=True)
    search_count = models.IntegerField(default=1)
    category = models.CharField(
        max_length=50,
        choices=[
            ("student_name", "Student Name"),
            ("course_name", "Course Name"),
            ("teacher_name", "Teacher Name"),
            ("subject", "Subject"),
            ("grade_level", "Grade Level"),
            ("general", "General"),
        ],
        default="general",
    )
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-search_count", "-last_searched"]
        indexes = [
            models.Index(fields=["term"]),
            models.Index(fields=["category", "-search_count"]),
        ]

    def __str__(self):
        return f"{self.term} ({self.search_count})"

    @classmethod
    def increment_count(cls, term, category="general"):
        """Increment search count for a term."""
        suggestion, created = cls.objects.get_or_create(
            term=term, defaults={"category": category}
        )
        if not created:
            suggestion.search_count += 1
            suggestion.save()
        return suggestion
