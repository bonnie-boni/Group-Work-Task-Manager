"""
Custom middleware for role-based access control
"""
from django.shortcuts import redirect
from django.urls import reverse
from .models import UserModel

class RoleRequiredMiddleware:
    """Middleware to attach user object to request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add user object to request if logged in
        user_id = request.session.get('user_id')
        if user_id:
            request.user_obj = UserModel.get_by_id(user_id)
        else:
            request.user_obj = None
        
        response = self.get_response(request)
        return response