from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal

from authentication.decorators import role_required
from parent_portal.views import get_current_child, get_parent_children
from .models import (
    LunchAccount, LunchTransaction, TransportationInfo, TransportationAlert,
    Activity, ActivityEnrollment, SupplyList, EventRSVP, 
    VolunteerOpportunity, VolunteerSignup
)
import logging

logger = logging.getLogger(__name__)


@login_required
@role_required(["Parent"])
def lunch_account_view(request):
    """Lunch account management for parents"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not current_child:
            return render(request, "school_services/lunch_account.html", {
                "error": "Please select a child to view lunch account information.",
                "children": children,
            })
        
        # Get or create lunch account
        lunch_account, created = LunchAccount.objects.get_or_create(
            student=current_child,
            defaults={'balance': Decimal('0.00')}
        )
        
        # Get recent transactions
        recent_transactions = lunch_account.transactions.all()[:20]
        
        # Handle fund addition
        if request.method == "POST":
            amount_str = request.POST.get('amount')
            payment_method = request.POST.get('payment_method', 'Credit Card')
            
            try:
                amount = Decimal(amount_str)
                if amount > 0:
                    transaction = lunch_account.add_funds(amount, payment_method)
                    messages.success(request, f"Successfully added ${amount} to lunch account.")
                    return redirect('school_services:lunch_account')
                else:
                    messages.error(request, "Amount must be greater than zero.")
            except (ValueError, TypeError):
                messages.error(request, "Invalid amount entered.")
        
        context = {
            "current_child": current_child,
            "children": children,
            "lunch_account": lunch_account,
            "recent_transactions": recent_transactions,
        }
        
        return render(request, "school_services/lunch_account.html", context)
        
    except Exception as e:
        logger.error(f"Error in lunch account view: {e}")
        return render(request, "school_services/lunch_account.html", {
            "error": "Unable to load lunch account information.",
            "children": children if 'children' in locals() else [],
        })


@login_required
@role_required(["Parent"])
def transportation_view(request):
    """Transportation information for students"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not current_child:
            return render(request, "school_services/transportation.html", {
                "error": "Please select a child to view transportation information.",
                "children": children,
            })
        
        # Get transportation info
        transportation, created = TransportationInfo.objects.get_or_create(
            student=current_child,
            defaults={'transport_type': 'PARENT'}
        )
        
        # Get relevant alerts
        alerts = []
        if transportation.bus_route:
            alerts = TransportationAlert.objects.filter(
                is_active=True,
                expires_at__gt=timezone.now()
            ).filter(
                Q(affected_routes__icontains=transportation.bus_route) |
                Q(affected_routes="")  # Affects all routes
            ).order_by('-created_at')
        
        context = {
            "current_child": current_child,
            "children": children,
            "transportation": transportation,
            "alerts": alerts,
        }
        
        return render(request, "school_services/transportation.html", context)
        
    except Exception as e:
        logger.error(f"Error in transportation view: {e}")
        return render(request, "school_services/transportation.html", {
            "error": "Unable to load transportation information.",
            "children": children if 'children' in locals() else [],
        })


@login_required
@role_required(["Parent"])
def activities_view(request):
    """View and enroll in extracurricular activities"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not current_child:
            return render(request, "school_services/activities.html", {
                "error": "Please select a child to view activities.",
                "children": children,
            })
        
        # Get available activities
        available_activities = Activity.objects.filter(
            is_active=True,
            registration_start__lte=timezone.now().date(),
            registration_end__gte=timezone.now().date()
        ).order_by('activity_type', 'name')
        
        # Get student's current enrollments
        enrollments = ActivityEnrollment.objects.filter(
            student=current_child
        ).select_related('activity')
        
        # Handle enrollment
        if request.method == "POST":
            activity_id = request.POST.get('activity_id')
            try:
                activity = Activity.objects.get(id=activity_id)
                can_enroll, reason = activity.can_student_enroll(current_child)
                
                if can_enroll:
                    enrollment = ActivityEnrollment.objects.create(
                        activity=activity,
                        student=current_child,
                        enrolled_by=request.user,
                        notes=request.POST.get('notes', '')
                    )
                    messages.success(request, f"Successfully enrolled in {activity.name}!")
                    return redirect('school_services:activities')
                else:
                    messages.error(request, f"Cannot enroll: {reason}")
            except Activity.DoesNotExist:
                messages.error(request, "Activity not found.")
        
        context = {
            "current_child": current_child,
            "children": children,
            "available_activities": available_activities,
            "enrollments": enrollments,
        }
        
        return render(request, "school_services/activities.html", context)
        
    except Exception as e:
        logger.error(f"Error in activities view: {e}")
        return render(request, "school_services/activities.html", {
            "error": "Unable to load activities information.",
            "children": children if 'children' in locals() else [],
        })


@login_required
@role_required(["Parent"])
def supply_lists_view(request):
    """School supply lists"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not current_child:
            return render(request, "school_services/supply_lists.html", {
                "error": "Please select a child to view supply lists.",
                "children": children,
            })
        
        # Get supply lists for student's grade
        supply_lists = SupplyList.objects.filter(
            Q(grade_level=str(current_child.grade_level)) |
            Q(grade_level="ALL")
        ).prefetch_related('items').order_by('subject', 'title')
        
        context = {
            "current_child": current_child,
            "children": children,
            "supply_lists": supply_lists,
        }
        
        return render(request, "school_services/supply_lists.html", context)
        
    except Exception as e:
        logger.error(f"Error in supply lists view: {e}")
        return render(request, "school_services/supply_lists.html", {
            "error": "Unable to load supply lists.",
            "children": children if 'children' in locals() else [],
        })


@login_required
@role_required(["Parent"])
def events_rsvp_view(request):
    """RSVP for school events"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        # Get upcoming events that allow RSVP
        from academics.models import SchoolCalendarEvent
        upcoming_events = SchoolCalendarEvent.objects.filter(
            start_date__gte=timezone.now().date(),
            requires_rsvp=True,
            is_active=True
        ).order_by('start_date')
        
        # Get existing RSVPs
        if current_child:
            existing_rsvps = EventRSVP.objects.filter(
                student=current_child,
                parent=request.user
            ).select_related('event')
        else:
            existing_rsvps = []
        
        # Handle RSVP submission
        if request.method == "POST":
            event_id = request.POST.get('event_id')
            rsvp_status = request.POST.get('rsvp_status')
            
            if not current_child:
                messages.error(request, "Please select a child first.")
                return redirect('school_services:events_rsvp')
            
            try:
                event = SchoolCalendarEvent.objects.get(id=event_id)
                rsvp, created = EventRSVP.objects.update_or_create(
                    event=event,
                    student=current_child,
                    parent=request.user,
                    defaults={
                        'rsvp_status': rsvp_status,
                        'number_attending': int(request.POST.get('number_attending', 1)),
                        'notes': request.POST.get('notes', '')
                    }
                )
                
                status_text = dict(EventRSVP.RSVP_STATUS)[rsvp_status]
                messages.success(request, f"RSVP updated: {status_text} for {event.title}")
                return redirect('school_services:events_rsvp')
                
            except (SchoolCalendarEvent.DoesNotExist, ValueError) as e:
                messages.error(request, "Invalid event or RSVP data.")
        
        context = {
            "current_child": current_child,
            "children": children,
            "upcoming_events": upcoming_events,
            "existing_rsvps": {rsvp.event_id: rsvp for rsvp in existing_rsvps},
        }
        
        return render(request, "school_services/events_rsvp.html", context)
        
    except Exception as e:
        logger.error(f"Error in events RSVP view: {e}")
        return render(request, "school_services/events_rsvp.html", {
            "error": "Unable to load events.",
            "children": children if 'children' in locals() else [],
        })


@login_required
@role_required(["Parent"])
def volunteer_opportunities_view(request):
    """View and sign up for volunteer opportunities"""
    try:
        # Get upcoming volunteer opportunities
        opportunities = VolunteerOpportunity.objects.filter(
            is_active=True,
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')
        
        # Get user's existing signups
        signups = VolunteerSignup.objects.filter(
            volunteer=request.user
        ).select_related('opportunity')
        
        # Handle signup
        if request.method == "POST":
            opportunity_id = request.POST.get('opportunity_id')
            
            try:
                opportunity = VolunteerOpportunity.objects.get(id=opportunity_id)
                
                if opportunity.spots_remaining > 0:
                    signup, created = VolunteerSignup.objects.get_or_create(
                        opportunity=opportunity,
                        volunteer=request.user,
                        defaults={
                            'notes': request.POST.get('notes', ''),
                            'contact_phone': request.POST.get('contact_phone', ''),
                            'emergency_contact': request.POST.get('emergency_contact', '')
                        }
                    )
                    
                    if created:
                        messages.success(request, f"Successfully signed up for {opportunity.title}!")
                    else:
                        messages.info(request, "You're already signed up for this opportunity.")
                else:
                    messages.error(request, "This volunteer opportunity is full.")
                    
                return redirect('school_services:volunteer_opportunities')
                
            except VolunteerOpportunity.DoesNotExist:
                messages.error(request, "Volunteer opportunity not found.")
        
        context = {
            "opportunities": opportunities,
            "signups": {signup.opportunity_id: signup for signup in signups},
        }
        
        return render(request, "school_services/volunteer_opportunities.html", context)
        
    except Exception as e:
        logger.error(f"Error in volunteer opportunities view: {e}")
        return render(request, "school_services/volunteer_opportunities.html", {
            "error": "Unable to load volunteer opportunities.",
        })


# API endpoints for mobile integration

@login_required
@role_required(["Parent"])
def lunch_balance_api(request):
    """API endpoint for quick lunch balance check"""
    try:
        children = get_parent_children(request.user)
        
        balance_data = []
        for child in children:
            try:
                lunch_account = LunchAccount.objects.get(student=child)
                balance_data.append({
                    'student_name': child.display_name,
                    'balance': float(lunch_account.balance),
                    'is_low': lunch_account.is_low_balance,
                    'last_transaction': lunch_account.transactions.first().transaction_date.isoformat() if lunch_account.transactions.exists() else None
                })
            except LunchAccount.DoesNotExist:
                balance_data.append({
                    'student_name': child.display_name,
                    'balance': 0.00,
                    'is_low': True,
                    'last_transaction': None
                })
        
        return JsonResponse({
            'balances': balance_data,
            'updated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in lunch balance API: {e}")
        return JsonResponse({'error': 'Unable to load balance data'}, status=500)
