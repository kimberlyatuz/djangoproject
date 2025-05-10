from django.shortcuts import redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for auth-related paths
        auth_paths = ['/login/', '/logout/', '/register/', '/unauthorized/']
        if any(request.path.startswith(path) for path in auth_paths):
            return self.get_response(request)

        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Skip middleware for these views
        if getattr(view_func, 'login_exempt', False):
            return None

        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')

        return None

















