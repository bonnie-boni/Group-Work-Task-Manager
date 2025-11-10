"""
Django Forms for Classroom Management
"""
from django import forms
from django.core.validators import EmailValidator
from datetime import datetime
from .models import GroupModel, ClassModel

class LoginForm(forms.Form):
    """User login form"""
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your password'
        })
    )
    role = forms.ChoiceField(
        choices=[('member', 'Member'), ('leader', 'Group Leader'), ('lecturer', 'Lecturer')],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )

class RegisterForm(forms.Form):
    """User registration form"""
    email = forms.EmailField(
        max_length=255,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your email'
        })
    )
    password = forms.CharField(
        min_length=6,
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter your password (min 6 characters)'
        })
    )
    confirm_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Confirm your password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        
        return cleaned_data

class ClassForm(forms.Form):
    """Form to create a class"""
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., AI101, Mathematics, Physics'
        })
    )
    password = forms.CharField(
        min_length=4,
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Class password (min 4 characters)'
        })
    )

class JoinClassForm(forms.Form):
    """Form to join a class"""
    class_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter class name'
        })
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Enter class password'
        })
    )

class TaskForm(forms.Form):
    """Form to create a task"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Task title'
        })
    )
    task_type = forms.ChoiceField(
        choices=[('text', 'Text Description'), ('file', 'File Upload')],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 5,
            'placeholder': 'Task description and requirements'
        })
    )
    task_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    due_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'datetime-local'
        })
    )

class GroupForm(forms.Form):
    """Form to create a group"""
    class_obj = forms.ChoiceField(
        choices=[], # Will be populated dynamically
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Group name'
        })
    )
    password = forms.CharField(
        min_length=4,
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Group password (min 4 characters)'
        })
    )

    def __init__(self, *args, **kwargs):
        leader_id = kwargs.pop('leader_id', None)
        super().__init__(*args, **kwargs)
        if leader_id:
            # Get classes where the current user is a leader
            classes = ClassModel.objects(members=leader_id).all()
            self.fields['class_obj'].choices = [(str(c.id), c.name) for c in classes]

    def clean_name(self):
        name = self.cleaned_data.get('name')
        class_id = self.cleaned_data.get('class_obj')

        if class_id and name:
            # Check if a group with the same name already exists in this class
            existing_group = GroupModel.objects(name=name, class_obj=class_id).first()
            if existing_group:
                raise forms.ValidationError("A group with this name already exists in this class.")
        return name


class WhitelistEmailForm(forms.Form):
    """Form to add email to whitelist"""
    email = forms.EmailField(
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'member@example.com'
        })
    )

class TaskDivisionForm(forms.Form):
    """Form to divide tasks among members"""
    member_id = forms.CharField(
        max_length=24,
        widget=forms.HiddenInput()
    )
    part_description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'Describe what this member should work on'
        })
    )

class SubmissionForm(forms.Form):
    """Form for member submission"""
    text_answer = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 15,
            'placeholder': 'Type your answer here...'
        })
    )
