from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import UserModel

def login_required(view_func):
    """
    Decorator to check if the user is logged in.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('login')
        
        # Attach user object to request for convenience
        request.user_obj = UserModel.get_by_id(user_id)
        if not request.user_obj:
            messages.error(request, 'User not found. Please log in again.')
            request.session.flush()
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def lecturer_required(view_func):
    """
    Decorator to check if the logged-in user is a lecturer.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('login')
        
        request.user_obj = UserModel.get_by_id(request.session.get('user_id'))
        if not request.user_obj or request.user_obj['role'] != UserModel.ROLE_LECTURER:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def leader_required(view_func):
    """
    Decorator to check if the logged-in user is a group leader or a member.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, 'You must be logged in to access this page.')
            return redirect('login')
        
        request.user_obj = UserModel.get_by_id(request.session.get('user_id'))
        if not request.user_obj or request.user_obj['role'] not in [UserModel.ROLE_LEADER, UserModel.ROLE_MEMBER]:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('dashboard')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view
