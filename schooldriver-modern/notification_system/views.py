from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count
from datetime import datetime, timedelta, date
import json

from .models import (
    Notification, NotificationPreference, ConferenceSchedule,
    NotificationTemplate, NotificationBatch
)
from .services import NotificationService, send_conference_reschedule_notification
from students.models import Student


@login_required
def notification_preferences(request):
    """View and update notification preferences"""
    
    try:
        preferences = request.user.notification_preferences
    except NotificationPreference.DoesNotExist:
        preferences = NotificationPreference.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        preferences.grade_frequency = request.POST.get('grade_frequency', preferences.grade_frequency)
        preferences.grade_delivery = request.POST.get('grade_delivery', preferences.grade_delivery)
        preferences.attendance_frequency = request.POST.get('attendance_frequency', preferences.attendance_frequency)
        preferences.attendance_delivery = request.POST.get('attendance_delivery', preferences.attendance_delivery)
        preferences.assignment_frequency = request.POST.get('assignment_frequency', preferences.assignment_frequency)
        preferences.assignment_delivery = request.POST.get('assignment_delivery', preferences.assignment_delivery)
        preferences.emergency_frequency = request.POST.get('emergency_frequency', preferences.emergency_frequency)
        preferences.emergency_delivery = request.POST.get('emergency_delivery', preferences.emergency_delivery)
        preferences.announcement_frequency = request.POST.get('announcement_frequency', preferences.announcement_frequency)
        preferences.announcement_delivery = request.POST.get('announcement_delivery', preferences.announcement_delivery)
        preferences.message_frequency = request.POST.get('message_frequency', preferences.message_frequency)
        preferences.message_delivery = request.POST.get('message_delivery', preferences.message_delivery)
        preferences.phone_number = request.POST.get('phone_number', preferences.phone_number)
        
        preferences.save()
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('notification_system:preferences')
    
    context = {
        'preferences': preferences,
        'frequency_choices': NotificationPreference.FREQUENCY_CHOICES,
        'delivery_choices': NotificationPreference.DELIVERY_CHOICES,
    }
    
    return render(request, 'notification_system/preferences.html', context)


@login_required
def notification_list(request):
    """List all notifications for the user"""
    
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('related_student').order_by('-created_at')
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        notifications = notifications.filter(category=category)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        notifications = notifications.filter(status=status)
    
    # Filter by student
    student_id = request.GET.get('student')
    if student_id:
        notifications = notifications.filter(related_student_id=student_id)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's students for filtering
    user_students = []
    if hasattr(request.user, 'parent_profile'):
        user_students = request.user.parent_profile.children.all()
    
    # Get categories for filtering
    categories = Notification.objects.filter(
        recipient=request.user
    ).values_list('category', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'user_students': user_students,
        'current_category': category,
        'current_status': status,
        'current_student': student_id,
    }
    
    return render(request, 'notification_system/notification_list.html', context)


@login_required
def notification_detail(request, notification_id):
    """View notification details and mark as read"""
    
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    # Mark as read if not already
    if notification.status != 'read':
        notification.mark_as_read()
    
    context = {
        'notification': notification,
    }
    
    return render(request, 'notification_system/notification_detail.html', context)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark notification as read via AJAX"""
    
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    
    notification.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'status': notification.status,
        'read_at': notification.read_at.isoformat() if notification.read_at else None
    })


@login_required
@require_http_methods(["POST"])
def mark_all_read(request):
    """Mark all notifications as read"""
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        status__in=['pending', 'sent', 'delivered']
    )
    
    count = unread_notifications.count()
    
    for notification in unread_notifications:
        notification.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'marked_count': count
    })


@login_required
def conference_schedule_list(request):
    """List conference schedules for the user"""
    
    if hasattr(request.user, 'parent_profile'):
        # Parent view - show booked conferences
        conferences = ConferenceSchedule.objects.filter(
            parent=request.user
        ).select_related('teacher', 'student').order_by('date', 'start_time')
    else:
        # Teacher view - show all their slots
        conferences = ConferenceSchedule.objects.filter(
            teacher=request.user
        ).select_related('parent', 'student').order_by('date', 'start_time')
    
    # Filter by status
    status = request.GET.get('status', 'all')
    if status != 'all':
        conferences = conferences.filter(status=status)
    
    # Filter by date range
    date_filter = request.GET.get('date_filter', 'upcoming')
    today = date.today()
    
    if date_filter == 'upcoming':
        conferences = conferences.filter(date__gte=today)
    elif date_filter == 'past':
        conferences = conferences.filter(date__lt=today)
    
    context = {
        'conferences': conferences,
        'current_status': status,
        'current_date_filter': date_filter,
        'status_choices': ConferenceSchedule.STATUS_CHOICES,
    }
    
    return render(request, 'notification_system/conference_list.html', context)


@login_required
def available_conference_slots(request, teacher_id=None):
    """View available conference slots for booking"""
    
    # Get available slots
    available_slots = ConferenceSchedule.objects.filter(
        status='available',
        date__gte=date.today()
    ).select_related('teacher').order_by('date', 'start_time')
    
    # Filter by teacher if specified
    if teacher_id:
        available_slots = available_slots.filter(teacher_id=teacher_id)
    
    # Get user's students for booking
    user_students = []
    if hasattr(request.user, 'parent_profile'):
        user_students = request.user.parent_profile.children.all()
    
    # Group by teacher and date
    slots_by_teacher = {}
    for slot in available_slots:
        teacher_name = slot.teacher.get_full_name()
        if teacher_name not in slots_by_teacher:
            slots_by_teacher[teacher_name] = {}
        
        date_str = slot.date.strftime('%Y-%m-%d')
        if date_str not in slots_by_teacher[teacher_name]:
            slots_by_teacher[teacher_name][date_str] = []
        
        slots_by_teacher[teacher_name][date_str].append(slot)
    
    context = {
        'slots_by_teacher': slots_by_teacher,
        'user_students': user_students,
    }
    
    return render(request, 'notification_system/available_slots.html', context)


@login_required
@require_http_methods(["POST"])
def book_conference(request, slot_id):
    """Book a conference slot"""
    
    slot = get_object_or_404(ConferenceSchedule, id=slot_id, status='available')
    student_id = request.POST.get('student_id')
    notes = request.POST.get('notes', '')
    
    if not student_id:
        return JsonResponse({'success': False, 'error': 'Student is required'})
    
    try:
        student = Student.objects.get(id=student_id)
        
        # Verify user is parent of this student
        if hasattr(request.user, 'parent_profile'):
            if student not in request.user.parent_profile.children.all():
                return JsonResponse({'success': False, 'error': 'Not authorized for this student'})
        
        # Book the slot
        slot.parent = request.user
        slot.student = student
        slot.status = 'booked'
        slot.booked_at = timezone.now()
        slot.notes = notes
        slot.save()
        
        # Send confirmation notifications
        from .services import send_conference_confirmation
        send_conference_confirmation(slot)
        
        return JsonResponse({
            'success': True,
            'message': 'Conference booked successfully!'
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def reschedule_conference(request, conference_id):
    """Reschedule an existing conference"""
    
    conference = get_object_or_404(
        ConferenceSchedule, 
        id=conference_id, 
        parent=request.user,
        status='booked'
    )
    
    if not conference.can_be_rescheduled():
        messages.error(request, 'Conference cannot be rescheduled (less than 24 hours notice required).')
        return redirect('notification_system:conference_list')
    
    # Get available slots from the same teacher
    available_slots = ConferenceSchedule.objects.filter(
        teacher=conference.teacher,
        status='available',
        date__gte=date.today()
    ).order_by('date', 'start_time')
    
    if request.method == 'POST':
        new_slot_id = request.POST.get('new_slot_id')
        
        try:
            new_slot = ConferenceSchedule.objects.get(
                id=new_slot_id, 
                teacher=conference.teacher,
                status='available'
            )
            
            # Perform rescheduling
            old_conference = conference
            new_conference = conference.reschedule_to(new_slot)
            
            # Send rescheduling notifications
            send_conference_reschedule_notification(old_conference, new_conference)
            
            messages.success(request, 'Conference rescheduled successfully!')
            return redirect('notification_system:conference_list')
            
        except ConferenceSchedule.DoesNotExist:
            messages.error(request, 'Selected slot is no longer available.')
        except ValueError as e:
            messages.error(request, str(e))
    
    context = {
        'conference': conference,
        'available_slots': available_slots,
    }
    
    return render(request, 'notification_system/reschedule_conference.html', context)


@login_required
@require_http_methods(["POST"])
def cancel_conference(request, conference_id):
    """Cancel a conference"""
    
    conference = get_object_or_404(
        ConferenceSchedule, 
        id=conference_id, 
        parent=request.user,
        status='booked'
    )
    
    cancellation_reason = request.POST.get('reason', '')
    
    # Cancel the conference
    conference.status = 'cancelled'
    conference.cancelled_at = timezone.now()
    conference.cancellation_reason = cancellation_reason
    conference.save()
    
    # Send cancellation notifications
    service = NotificationService()
    
    # Notify teacher
    service.send_notification(
        recipient=conference.teacher,
        template_name='conference_cancelled',
        context={
            'parent_name': conference.parent.get_full_name(),
            'student_name': conference.student.full_name,
            'date': conference.date,
            'time': conference.start_time,
            'reason': cancellation_reason,
        },
        priority='normal'
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Conference cancelled successfully.'
    })


@login_required
def notification_dashboard(request):
    """Notification dashboard with statistics"""
    
    # Get notification statistics
    stats = {
        'total': Notification.objects.filter(recipient=request.user).count(),
        'unread': Notification.objects.filter(
            recipient=request.user, 
            status__in=['pending', 'sent', 'delivered']
        ).count(),
        'read': Notification.objects.filter(
            recipient=request.user, 
            status='read'
        ).count(),
    }
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:10]
    
    # Get notifications by category
    category_stats = Notification.objects.filter(
        recipient=request.user
    ).values('category').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get upcoming conferences
    upcoming_conferences = ConferenceSchedule.objects.filter(
        parent=request.user,
        status='booked',
        date__gte=date.today()
    ).order_by('date', 'start_time')[:5]
    
    context = {
        'stats': stats,
        'recent_notifications': recent_notifications,
        'category_stats': category_stats,
        'upcoming_conferences': upcoming_conferences,
    }
    
    return render(request, 'notification_system/dashboard.html', context)


@login_required
def send_test_notification(request):
    """Send a test notification (for testing purposes)"""
    
    if request.method == 'POST':
        delivery_method = request.POST.get('delivery_method', 'email')
        
        service = NotificationService()
        
        notifications = service.send_notification(
            recipient=request.user,
            template_name='test_notification',
            context={
                'user_name': request.user.get_full_name() or request.user.username,
                'test_timestamp': timezone.now(),
            },
            delivery_methods=[delivery_method],
            priority='low'
        )
        
        if notifications:
            messages.success(request, f'Test {delivery_method} notification sent!')
        else:
            messages.error(request, f'Failed to send test {delivery_method} notification.')
        
        return redirect('notification_system:preferences')
    
    return redirect('notification_system:preferences')
