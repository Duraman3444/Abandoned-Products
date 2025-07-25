from django.urls import path
from . import views

app_name = "school_services"

urlpatterns = [
    # Lunch Account Management
    path("lunch-account/", views.lunch_account_view, name="lunch_account"),
    
    # Transportation
    path("transportation/", views.transportation_view, name="transportation"),
    
    # Activities
    path("activities/", views.activities_view, name="activities"),
    
    # Supply Lists
    path("supply-lists/", views.supply_lists_view, name="supply_lists"),
    
    # Event RSVP
    path("events-rsvp/", views.events_rsvp_view, name="events_rsvp"),
    
    # Volunteer Opportunities
    path("volunteer-opportunities/", views.volunteer_opportunities_view, name="volunteer_opportunities"),
    
    # API endpoints
    path("api/lunch-balance/", views.lunch_balance_api, name="lunch_balance_api"),
]
