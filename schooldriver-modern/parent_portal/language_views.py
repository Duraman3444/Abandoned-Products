from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils import translation
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.conf import settings
from schooldriver_modern.models import UserProfile


@login_required
@require_POST
@csrf_protect
def set_language_view(request):
    """Set user's language preference and update their profile"""
    language = request.POST.get('language')
    
    # Validate language choice
    valid_languages = [lang[0] for lang in settings.LANGUAGES]
    if language not in valid_languages:
        messages.error(request, "Invalid language selection.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Update user's profile language preference
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.preferred_language = language
        profile.save()
        
        # Activate the language for the current session
        translation.activate(language)
        request.session['django_language'] = language
        
        # Get language display name
        language_name = dict(settings.LANGUAGES).get(language, language)
        messages.success(request, f"Language changed to {language_name}.")
        
    except Exception as e:
        messages.error(request, "Failed to update language preference.")
    
    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', '/'))


def get_user_language(user):
    """Get user's preferred language from their profile"""
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.preferred_language
    except UserProfile.DoesNotExist:
        return settings.LANGUAGE_CODE
