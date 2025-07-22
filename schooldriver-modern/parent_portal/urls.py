from django.urls import path
from . import views

app_name = "parent_portal"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("children/", views.children_view, name="children"),
    path("grades/<int:student_id>/", views.grades_view, name="grades"),
    path("messages/", views.messages_view, name="messages"),
    path("profile/", views.profile_view, name="profile"),
]
