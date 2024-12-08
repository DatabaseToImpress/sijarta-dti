from django.shortcuts import redirect
from django.urls import reverse

class AuthenticationMiddleware:
    """
    Middleware to ensure all views (except public ones) require authentication.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Define public paths that do not require authentication
        public_paths = [
            reverse('landing'),
            reverse('login'),
            reverse('register'),
            reverse('register_user'),
            reverse('register_worker'),
        ]

        # If the request path is public, allow it
        if request.path in public_paths:
            return self.get_response(request)

        # If the user is not authenticated, redirect to login
        if not request.session.get('user_id'):
            return redirect('landing')

        # Proceed to the requested view
        return self.get_response(request)
