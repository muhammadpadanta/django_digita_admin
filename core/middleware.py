# core/middleware.py

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout

class AdminSessionTimeoutMiddleware:
    """
    Middleware to enforce session timeout specifically for admin users.

    This middleware checks on every request if the logged-in user is an admin
    (superuser or staff).
    - If they are an admin, it sets their session to expire after a specific
      period of inactivity (defined by settings.SESSION_COOKIE_AGE).
    - If they are a regular authenticated user, it can be configured to give
      them a longer session or a session that lasts until the browser closes.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before it reaches the view

        # We only care about authenticated users
        if request.user.is_authenticated:
            # Check if the user is an admin (is_staff for admin panel access, is_superuser for all permissions)
            if request.user.is_superuser or request.user.is_staff:
                # For admins, we enforce the inactivity timeout defined in settings.py
                # The session expiry is reset on each request because of SESSION_SAVE_EVERY_REQUEST = True
                # No specific action is needed here, as they will fall under the global
                # SESSION_COOKIE_AGE setting. We just don't give them an extended session.
                pass
            else:
                # For regular, non-admin users, we can override the global setting.
                # Setting expiry to 0 makes the session last until the browser is closed.
                # Alternatively, you could set a longer duration in seconds, e.g., 86400 for 24 hours.
                request.session.set_expiry(0)

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

