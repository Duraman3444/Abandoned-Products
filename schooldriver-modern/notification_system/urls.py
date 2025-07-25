from django.urls import path
from . import views

app_name = 'notification_system'

urlpatterns = [
    # Notification management
    path('', views.notification_dashboard, name='dashboard'),
    path('list/', views.notification_list, name='list'),
    path('preferences/', views.notification_preferences, name='preferences'),
    path('<int:notification_id>/', views.notification_detail, name='detail'),
    
    # AJAX endpoints
    path('<int:notification_id>/read/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('test/', views.send_test_notification, name='send_test'),
    
    # Conference scheduling
    path('conferences/', views.conference_schedule_list, name='conference_list'),
    path('conferences/available/', views.available_conference_slots, name='available_slots'),
    path('conferences/available/<int:teacher_id>/', views.available_conference_slots, name='available_slots_teacher'),
    path('conferences/<int:slot_id>/book/', views.book_conference, name='book_conference'),
    path('conferences/<int:conference_id>/reschedule/', views.reschedule_conference, name='reschedule_conference'),
    path('conferences/<int:conference_id>/cancel/', views.cancel_conference, name='cancel_conference'),
]
