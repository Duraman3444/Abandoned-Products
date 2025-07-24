from django.utils import translation
from django.conf import settings
from schooldriver_modern.models import UserProfile


class UserLanguageMiddleware:
    """Middleware to set user's preferred language from their profile"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set language based on user's profile preference
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                user_language = profile.preferred_language
                
                # Validate the language is supported
                supported_languages = [lang[0] for lang in settings.LANGUAGES]
                if user_language in supported_languages:
                    # Check if language is already set in session
                    session_language = request.session.get('django_language')
                    
                    # Only activate if different from session or session is empty
                    if session_language != user_language:
                        translation.activate(user_language)
                        request.session['django_language'] = user_language
                        
            except UserProfile.DoesNotExist:
                # User profile doesn't exist, use default language
                pass
        
        response = self.get_response(request)
        return response
