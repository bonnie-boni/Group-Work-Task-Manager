"""
Context processors to make user data available in all templates
"""

def user_context(request):
    """Add user information to template context"""
    user_obj = getattr(request, 'user_obj', None)
    
    return {
        'current_user': user_obj,
        'is_authenticated': user_obj is not None,
        'is_lecturer': user_obj and user_obj['role'] == 'lecturer',
        'is_leader': user_obj and user_obj['role'] == 'leader',
        'is_member': user_obj and user_obj['role'] == 'member',
    }