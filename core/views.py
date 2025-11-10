"""
Views for Classroom Management System
"""
import os
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from bson.objectid import ObjectId

from .models import (
    UserModel, ClassModel, GroupModel, TaskModel,
    SubmissionModel, CompiledSubmissionModel
)
from .forms import (
    LoginForm, RegisterForm, ClassForm, TaskForm,
    GroupForm, WhitelistEmailForm, TaskDivisionForm,
    SubmissionForm, JoinClassForm
)
from .decorators import login_required, lecturer_required, leader_required
from .pdf_utils import generate_member_pdf, compile_group_pdf, get_submission_pdf_path, generate_compiled_pdf_from_text
from django.conf import settings
import mimetypes # Move this import to the top


# ============= AUTHENTICATION VIEWS =============

@ratelimit(key='ip', rate='5/m', method='POST')
def login_view(request):
    """User login"""
    if request.session.get('user_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            selected_role = form.cleaned_data['role']

            user = UserModel.authenticate(email, password)
            
            if user:
                if user.role == selected_role:
                    request.session['user_id'] = str(user.id)
                    request.session['user_email'] = user.email
                    request.session['user_role'] = user.role
                    messages.success(request, f"Welcome back, {user.email}!")
                    return redirect('dashboard')
                else:
                    messages.error(request, f"Login failed. Your account role is '{user.role}', but you tried to log in as '{selected_role}'.")
            else:
                messages.error(request, 'Invalid email or password')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})

@ratelimit(key='ip', rate='3/m', method='POST')
def register_view(request):
    """User registration"""
    if request.session.get('user_id'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            if UserModel.get_by_email(email):
                messages.error(request, 'Email already registered')
            else:
                user = UserModel.create(email, password, role=UserModel.ROLE_MEMBER)
                if user:
                    request.session['user_id'] = str(user.id)
                    request.session['user_email'] = user.email
                    request.session['user_role'] = user.role
                    messages.success(request, 'Registration successful! Please log in.')
                    return redirect('login')
                else:
                    messages.error(request, 'Registration failed. Please try again.')
    else:
        form = RegisterForm()
    
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    """User logout"""
    request.session.flush()
    messages.success(request, 'Logged out successfully')
    return redirect('login')


# ============= DASHBOARD VIEWS =============

@login_required
def dashboard_view(request):
    """Main dashboard - redirects based on role"""
    user_id = request.session.get('user_id')
    user_obj = UserModel.get_by_id(user_id)
    role = user_obj['role']
    
    if role == 'lecturer':
        return redirect('lecturer_dashboard')
    elif role == 'leader':
        return redirect('leader_dashboard')
    else:
        return redirect('member_dashboard')


# ============= LECTURER VIEWS =============

@lecturer_required
def lecturer_dashboard(request):
    """Lecturer dashboard"""
    user_id = request.session.get('user_id')
    classes = ClassModel.get_by_lecturer(user_id)
    
    context = {
        'classes': classes
    }
    return render(request, 'lecturer/dashboard.html', context)

@lecturer_required
def create_class(request):
    """Create a new class"""
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            user_id = request.session.get('user_id')
            
            class_obj = ClassModel.create(name, password, user_id)
            messages.success(request, f'Class "{name}" created successfully! Class ID: {class_obj.id}')
            return redirect('lecturer_dashboard')
    else:
        form = ClassForm()
    
    return render(request, 'lecturer/create_class.html', {'form': form})

@lecturer_required
def class_detail(request, class_id):
    """View class details and manage tasks"""
    class_obj = ClassModel.get_by_id(class_id)
    
    if not class_obj:
        messages.error(request, 'Class not found')
        return redirect('lecturer_dashboard')
    
    # Verify lecturer owns this class
    if str(class_obj.lecturer.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access')
        return redirect('lecturer_dashboard')
    
    tasks = TaskModel.get_by_class(str(class_obj.id))
    groups = GroupModel.get_by_class(str(class_obj.id))
    
    context = {
        'class_obj': class_obj,
        'tasks': tasks,
        'groups': groups
    }
    return render(request, 'lecturer/class_detail.html', context)

@lecturer_required
def create_task(request, class_id):
    """Create a new task for a class"""
    class_obj = ClassModel.get_by_id(class_id)

    if not class_obj or str(class_obj.lecturer.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access')
        return redirect('lecturer_dashboard')

    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            task_type = form.cleaned_data['task_type']
            description = form.cleaned_data.get('description')
            task_file = request.FILES.get('task_file')
            due_date = form.cleaned_data.get('due_date')

            file_path = None
            if task_type == 'file' and task_file:
                # Save the file
                upload_dir = os.path.join(settings.MEDIA_ROOT, 'tasks')
                os.makedirs(upload_dir, exist_ok=True)
                file_name = task_file.name
                full_file_path = os.path.join(upload_dir, file_name)
                with open(full_file_path, 'wb+') as destination:
                    for chunk in task_file.chunks():
                        destination.write(chunk)
                file_path = os.path.join('tasks', file_name)  # Relative path for DB

            task = TaskModel.create(
                str(class_obj.id),
                request.session.get('user_id'),
                title,
                description=description if task_type == 'text' else None,
                file_path=file_path if task_type == 'file' else None,
                due_date=due_date
            )
            messages.success(request, f'Task "{title}" created successfully!')
            return redirect('class_detail', class_id=class_id)
    else:
        form = TaskForm()

    context = {
        'form': form,
        'class_obj': class_obj
    }
    return render(request, 'lecturer/create_task.html', context)

@lecturer_required
def view_submissions(request, task_id):
    """View all submissions for a task"""
    task = TaskModel.get_by_id(task_id)

    if not task or str(task.lecturer.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access to view submissions')
        return redirect('lecturer_dashboard')
    
    # Get compiled submissions for this task
    compiled_subs = CompiledSubmissionModel.get_by_task(task_id)
    
    # Get groups for this class
    groups = GroupModel.get_by_class(str(task.class_obj.id))
    
    # Map compiled submissions to groups
    submission_map = {}
    for comp_sub in compiled_subs:
        submission_map[str(comp_sub.group.id)] = comp_sub
    
    context = {
        'task': task,
        'groups': groups,
        'submission_map': submission_map
    }
    return render(request, 'lecturer/view_submissions.html', context)


# ============= GROUP LEADER VIEWS =============

@leader_required
def leader_dashboard(request):
    """Group leader dashboard"""
    user_id = request.session.get('user_id')
    
    # Get groups where user is leader
    led_groups = GroupModel.get_by_leader(user_id)
    
    # Get groups where user is member (for tasks)
    member_groups = GroupModel.get_by_member(user_id)
    
    # Get the class the leader has joined
    joined_class = None
    if member_groups:
        # For simplicity, assume the leader is part of one class
        class_id = member_groups[0].class_obj.id
        joined_class = ClassModel.get_by_id(class_id)
    
    context = {
        'led_groups': led_groups,
        'member_groups': member_groups,
        'joined_class': joined_class
    }
    return render(request, 'leader/dashboard.html', context)

@leader_required
def create_group(request):
    """Create a new group"""
    user_id = request.session.get('user_id')
    
    # A user becomes a leader by joining a class.
    # We need to find which class they are a leader of.
    # For simplicity, we'll assume a leader can only be part of one class.
    # A better implementation would allow the user to select a class.
    
    # Find the class this leader is associated with.
    # This is a simplified approach. A more robust solution would be needed
    # if a leader can join multiple classes.
    all_classes = ClassModel.objects()
    class_for_leader = None
    for cls in all_classes:
        if user_id in getattr(cls, 'leaders', []): # Assuming a 'leaders' list in ClassModel
            class_for_leader = cls
            break
    
    # If not found via a 'leaders' list, we need another way to associate them.
    # The current model doesn't directly link leaders to classes they've joined.
    # Let's modify this logic. A leader who has joined a class can create a group.
    # The create_group form will need a way to specify the class.
    
    # For now, let's assume the leader has to join a class first,
    # and we'll need to adjust the logic to find that class.
    # The `create_group` view needs to know which class to create the group in.
    
    if request.method == 'POST':
        form = GroupForm(request.POST, leader_id=user_id)
        if form.is_valid():
            name = form.cleaned_data['name']
            password = form.cleaned_data['password']
            class_id = form.cleaned_data['class_obj'] # Get class_id from the form
            
            group = GroupModel.create(class_id, user_id, name, password)
            
            messages.success(request, f'Group "{name}" created successfully! Group ID: {group.id}')
            return redirect('group_detail', group_id=str(group.id))
    else:
        form = GroupForm(leader_id=user_id) # Pass leader_id to populate class choices
    
    context = {
        'form': form,
    }
    return render(request, 'leader/create_group.html', context)

@login_required
def join_class_view(request):
    """Join an existing class"""
    if request.method == 'POST':
        form = JoinClassForm(request.POST)
        if form.is_valid():
            class_name = form.cleaned_data['class_name']
            password = form.cleaned_data['password']
            user_id = request.session.get('user_id')
            
            class_obj = ClassModel.get_by_name(class_name)
            
            if not class_obj:
                messages.error(request, 'Class not found')
            elif not ClassModel.verify_password(class_name, password):
                messages.error(request, 'Invalid password')
            else:
                # Add user to class as a leader
                ClassModel.add_leader(class_obj.id, user_id)
                # Update user role
                UserModel.update_role(user_id, UserModel.ROLE_LEADER)
                request.session['user_role'] = UserModel.ROLE_LEADER
                messages.success(request, f'Successfully joined class "{class_name}"')
                return redirect('leader_dashboard')
    else:
        form = JoinClassForm()
    
    return render(request, 'leader/join_class.html', {'form': form})

@login_required
def accept_group_invitation(request, group_id):
    """Accept an invitation to join a group"""
    user_id = request.session.get('user_id')
    user_email = request.session.get('user_email')
    
    group = GroupModel.get_by_id(group_id)
    
    if not group:
        messages.error(request, 'Group not found.')
        return redirect('member_dashboard')
    
    if user_email not in group.whitelist_emails:
        messages.error(request, 'You are not whitelisted for this group.')
        return redirect('member_dashboard')
    
    if user_id in [str(m.id) for m in group.members]:
        messages.info(request, 'You are already a member of this group.')
        return redirect('member_dashboard')
    
    # Add member to the group
    GroupModel.add_member(group_id, user_id)
    
    # Optionally, remove email from whitelist after joining
    # GroupModel.remove_whitelist_email(group_id, user_email)
    
    messages.success(request, f'Successfully joined group "{group.name}"!')
    return redirect('member_dashboard')

@leader_required
def group_detail(request, group_id):
    """View group details and manage members"""
    group = GroupModel.get_by_id(group_id)
    
    if not group or str(group.leader.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access')
        return redirect('leader_dashboard')
    
    # Get class information
    class_obj = ClassModel.get_by_id(group.class_obj.id)
    
    # Get all tasks for this class
    tasks = TaskModel.get_by_class(str(group.class_obj.id))
    
    # Get member details
    members = []
    for member_obj in group.members:
        member = UserModel.get_by_id(str(member_obj.id))
        if member:
            members.append(member)
    
    # Get submissions for each task in this group
    submissions_by_task = {}
    for task_obj in tasks:
        task_submissions = SubmissionModel.get_by_task_and_group(str(task_obj.id), str(group.id))
        
        # Attach member info to each submission
        for sub in task_submissions:
            sub.member_obj = UserModel.get_by_id(sub.member.id)
        
        submissions_by_task[str(task_obj.id)] = task_submissions
    
    context = {
        'group': group,
        'class_obj': class_obj,
        'tasks': tasks,
        'members': members,
        'submissions_by_task': submissions_by_task,
    }
    return render(request, 'leader/group_detail.html', context)

@leader_required
def add_whitelist(request, group_id):
    """Add email to group whitelist"""
    group = GroupModel.get_by_id(group_id)
    
    if not group or str(group.leader.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access')
        return redirect('leader_dashboard')
    
    if request.method == 'POST':
        form = WhitelistEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            GroupModel.add_whitelist_email(group_id, email)
            messages.success(request, f'Email {email} added to whitelist')
            return redirect('group_detail', group_id=group_id)
    
    return redirect('group_detail', group_id=group_id)

@leader_required
def remove_whitelist(request, group_id, email):
    """Remove email from whitelist"""
    group = GroupModel.get_by_id(group_id)
    
    if not group or str(group.leader.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access')
        return redirect('leader_dashboard')
    
    GroupModel.remove_whitelist_email(group_id, email)
    messages.success(request, f'Email {email} removed from whitelist')
    return redirect('group_detail', group_id=group_id)

@leader_required
def divide_task(request, group_id, task_id):
    """Divide task among group members"""
    group = GroupModel.get_by_id(group_id)
    task = TaskModel.get_by_id(task_id)
    
    if not group or str(group.leader.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access')
        return redirect('leader_dashboard')
    
    if not task:
        messages.error(request, 'Task not found')
        return redirect('group_detail', group_id=group_id)
    
    # Get member details
    members = []
    for member_obj in group.members:
        member = UserModel.get_by_id(str(member_obj.id))
        if member:
            members.append(member)
    
    if request.method == 'POST':
        # Process task divisions
        for member in members:
            part_desc = request.POST.get(f'part_{str(member.id)}')
            if part_desc and part_desc.strip():
                TaskModel.add_division(task_id, str(member.id), part_desc)
        
        messages.success(request, 'Task divisions saved successfully')
        return redirect('group_detail', group_id=group_id)
    
    context = {
        'group': group,
        'task': task,
        'members': members
    }
    return render(request, 'leader/divide_task.html', context)

@leader_required
def compile_submission(request, group_id, task_id):
    """Compile group submissions into one PDF from curated text"""
    group = GroupModel.get_by_id(group_id)
    task = TaskModel.get_by_id(task_id)
    
    if not group or str(group.leader.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access')
        return redirect('leader_dashboard')
    
    if not task:
        messages.error(request, 'Task not found')
        return redirect('group_detail', group_id=group_id)
    
    if request.method == 'POST':
        compiled_text_content = request.POST.get('compiled_text_content', '')
        
        if not compiled_text_content.strip():
            messages.error(request, 'Compiled text cannot be empty.')
            return redirect('leader_compile_submissions_view', group_id=group_id, task_id=task_id)

        # Get member details for the PDF
        members_data = []
        for member_obj in group.members:
            member = UserModel.get_by_id(str(member_obj.id))
            if member:
                members_data.append({'email': member.email})

        # Generate PDF from the compiled text
        compiled_pdf_path = generate_compiled_pdf_from_text(
            compiled_text_content,
            group.name,
            task.title,
            members_data # Pass members data
        )
        
        if compiled_pdf_path:
            relative_path = compiled_pdf_path.replace(settings.MEDIA_ROOT, '').lstrip('/')
            
            # Check if a compiled submission already exists for this task and group
            existing_compiled_sub = CompiledSubmissionModel.get_by_task_and_group(task_id, group_id)
            
            if existing_compiled_sub:
                # Update existing compiled submission
                existing_compiled_sub.compiled_pdf_path = f'/media/{relative_path}'
                existing_compiled_sub.save()
                messages.success(request, 'Compiled submission updated successfully!')
            else:
                # Create new compiled submission
                CompiledSubmissionModel.create(group_id, task_id, f'/media/{relative_path}')
                messages.success(request, 'Submissions compiled successfully!')
            
            return redirect('group_detail', group_id=group_id)
        else:
            messages.error(request, 'Failed to generate compiled PDF.')
            return redirect('leader_compile_submissions_view', group_id=group_id, task_id=task_id)
    
    # If not a POST request, redirect to the view-and-compile page
    return redirect('leader_compile_submissions_view', group_id=group_id, task_id=task_id)


# ============= MEMBER VIEWS =============

@login_required
def member_dashboard(request):
    """Member dashboard"""
    user_id = request.session.get('user_id')
    
    # Get groups user is a member of
    member_of_groups = GroupModel.get_by_member(user_id)
    
    # Get groups where user's email is whitelisted but they are not yet a member
    user_email = request.session.get('user_email')
    invited_groups = GroupModel.objects(whitelist_emails=user_email, members__ne=user_id)

    # Get the class(es) the member belongs to via their groups
    member_classes_ids = set()
    for group in member_of_groups:
        member_classes_ids.add(str(group.class_obj.id))
    
    # Get all unique tasks from classes the member is part of
    all_class_tasks_set = set()
    for group in member_of_groups:
        tasks_in_group_class = TaskModel.get_by_class(str(group.class_obj.id))
        for task in tasks_in_group_class:
            all_class_tasks_set.add(task)
    all_class_tasks = list(all_class_tasks_set)

    # Get tasks for each group the user is a member of (for task divisions)
    group_tasks_with_divisions = {}
    for group in member_of_groups:
        tasks = TaskModel.get_by_class(str(group.class_obj.id))
        member_tasks_with_divisions = []
        for task in tasks:
            # Ensure explicit string comparison for member_id
            if any(str(div.get('member_id')) == str(user_id) for div in task.divisions):
                # Check if member has submitted this task
                has_submitted = SubmissionModel.get_by_task_and_member(str(task.id), user_id) is not None
                task.has_submitted = has_submitted # Add submission status to task object
                member_tasks_with_divisions.append(task)
        
        group_tasks_with_divisions[str(group.id)] = member_tasks_with_divisions
    
    context = {
        'member_of_groups': member_of_groups,
        'invited_groups': invited_groups,
        'all_class_tasks': all_class_tasks, # All unique tasks from classes the member is in
        'group_tasks_with_divisions': group_tasks_with_divisions # Tasks specifically divided for the member, with submission status
    }
    return render(request, 'member/dashboard.html', context)

@login_required
def submit_task(request, task_id):
    """Submit task answer"""
    task = TaskModel.get_by_id(task_id)
    user_id = request.session.get('user_id')
    user_email = request.session.get('user_email')
    
    if not task:
        messages.error(request, 'Task not found')
        return redirect('member_dashboard')
    
    # Find which group this task belongs to for this user
    groups = GroupModel.get_by_member(user_id)
    user_group = None
    for group in groups:
        if str(group.class_obj.id) == str(task.class_obj.id):
            user_group = group
            break
    
    if not user_group:
        messages.error(request, 'You are not in a group for this class')
        return redirect('member_dashboard')
    
    # Check if already submitted
    existing_sub = SubmissionModel.get_by_task_and_member(task_id, user_id)
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            text_answer = form.cleaned_data['text_answer']
            
            # Generate PDF
            pdf_path = generate_member_pdf(
                text_answer,
                user_email,
                task.title
            )
            
            if pdf_path:
                relative_path = pdf_path.replace(settings.MEDIA_ROOT, '').lstrip('/')
                
                if existing_sub:
                    # Update existing submission
                    existing_sub.text_answer = text_answer
                    existing_sub.pdf_path = f'/media/{relative_path}'
                    existing_sub.save() # Save the updated submission
                    messages.success(request, 'Submission updated successfully!')
                    
                    # Notify group leader
                    leader_email = user_group.leader.email
                    messages.info(request, f'Your submission for "{task.title}" has been updated. Group leader ({leader_email}) has been notified.')
                else:
                    # Create new submission
                    SubmissionModel.create(
                        task_id,
                        str(user_group.id),
                        user_id,
                        text_answer,
                        f'/media/{relative_path}'
                    )
                    messages.success(request, 'Submission successful!')
                
                return redirect('member_dashboard')
            else:
                messages.error(request, 'Failed to generate PDF')
    else:
        # Pre-fill if already submitted
        initial_data = {}
        if existing_sub:
            initial_data['text_answer'] = existing_sub.text_answer
        
        form = SubmissionForm(initial=initial_data)
    
    # Get member's part of the task
    member_part = None
    for div in task.divisions:
        if div.get('member_id') == user_id:
            member_part = div.get('part_description')
            break
    
    context = {
        'task': task,
        'form': form,
        'member_part': member_part,
        'existing_submission': existing_sub
    }
    return render(request, 'member/submit_task.html', context)


# ============= FILE DOWNLOAD VIEWS =============

@login_required
def download_compiled(request, group_id, task_id):
    """Download compiled group submission"""
    compiled = CompiledSubmissionModel.get_by_task_and_group(task_id, group_id)
    
    if not compiled:
        raise Http404("Compiled submission not found")
    
    # Verify access rights
    user_obj = request.user_obj
    group = GroupModel.get_by_id(group_id)
    task = TaskModel.get_by_id(task_id)
    
    # Allow access if: lecturer, group leader, or group member
    is_lecturer = user_obj.role == 'lecturer' and task and str(task.lecturer.id) == str(user_obj.id)
    is_leader = group and str(group.leader.id) == str(user_obj.id)
    is_member = group and str(user_obj.id) in [str(m.id) for m in group.members]
    
    if not (is_lecturer or is_leader or is_member):
        messages.error(request, 'Unauthorized access')
        return redirect('dashboard')
    
    # Get file path
    pdf_path = get_submission_pdf_path(compiled.compiled_pdf_path)
    
    if not os.path.exists(pdf_path):
        raise Http404("File not found")
    
    return FileResponse(
        open(pdf_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(pdf_path)
    )

@login_required
def download_task_file(request, task_id):
    """Download a task file"""
    task = TaskModel.get_by_id(task_id)

    if not task or not task.file_path:
        raise Http404("Task or file not found")

    # Verify access rights: member of the class the task belongs to
    user_id = request.session.get('user_id')
    
    # Get groups user is a member of
    member_of_groups = GroupModel.get_by_member(user_id)
    
    # Get the class(es) the member belongs to via their groups
    member_classes_ids = set()
    for group in member_of_groups:
        member_classes_ids.add(str(group.class_obj.id))
    
    is_member_of_class = str(task.class_obj.id) in member_classes_ids
    
    if not is_member_of_class:
        messages.error(request, 'Unauthorized access to download this task file.')
        return redirect('member_dashboard')

    file_full_path = os.path.join(settings.MEDIA_ROOT, task.file_path)

    if not os.path.exists(file_full_path):
        raise Http404("File not found on server")
    
    # Guess the MIME type based on the file extension
    content_type, encoding = mimetypes.guess_type(file_full_path)
    if content_type is None:
        content_type = 'application/octet-stream' # Default if type cannot be guessed

    return FileResponse(
        open(file_full_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(file_full_path),
        content_type=content_type
    )

@leader_required
def leader_compile_submissions_view(request, group_id, task_id):
    """
    Leader can view all member submissions for a task in a text area
    and then trigger compilation.
    """
    group = GroupModel.get_by_id(group_id)
    task = TaskModel.get_by_id(task_id)

    if not group or str(group.leader.id) != request.session.get('user_id'):
        messages.error(request, 'Unauthorized access')
        return redirect('leader_dashboard')
    
    if not task:
        messages.error(request, 'Task not found')
        return redirect('group_detail', group_id=group_id)

    submissions = SubmissionModel.get_by_task_and_group(task_id, group_id)
    
    # Attach member info to each submission
    for sub in submissions:
        member = UserModel.get_by_id(sub.member.id)
        if member:
            sub.member_obj = member
        else:
            sub.member_obj = {'email': 'Unknown Member'} # Provide a fallback

    context = {
        'group': group,
        'task': task,
        'submissions': submissions, # Pass individual submissions
        'has_submissions': bool(submissions)
    }
    return render(request, 'leader/compile_submissions_view.html', context)


# ============= POLLING API VIEWS =============

@login_required
@require_http_methods(["GET"])
def poll_tasks(request, class_id):
    """API endpoint to poll for task updates"""
    class_obj = ClassModel.get_by_id(class_id)
    if not class_obj:
        return JsonResponse({'tasks': []})
    tasks = TaskModel.get_by_class(str(class_obj.id))
    
    task_list = []
    for task in tasks:
        task_list.append({
            'id': str(task.id),
            'title': task.title,
            'description': task.description,
            'created_at': task.created_at.isoformat() if task.created_at else None,
            'due_date': task.due_date.isoformat() if task.due_date else None
        })
    
    return JsonResponse({'tasks': task_list})

@login_required
@require_http_methods(["GET"])
def poll_submissions(request, task_id, group_id):
    """API endpoint to poll for submission updates"""
    submissions = SubmissionModel.get_by_task_and_group(task_id, group_id)
    
    sub_list = []
    for sub in submissions:
        user = UserModel.get_by_id(sub.member.id)
        sub_list.append({
            'id': str(sub.id),
            'member_email': user.email if user else 'Unknown',
            'status': sub.status,
            'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else None
        })
    
    return JsonResponse({'submissions': sub_list})

@login_required
def download_submission_pdf(request, submission_id):
    """Download an individual submission PDF"""
    submission = SubmissionModel.get_by_id(submission_id)

    if not submission or not submission.pdf_path:
        raise Http404("Submission or PDF not found")

    # Verify access rights: leader of the group this submission belongs to
    user_id = request.session.get('user_id')
    group = GroupModel.get_by_id(submission.group.id)
    
    is_leader = group and str(group.leader.id) == user_id

    if not is_leader:
        messages.error(request, 'Unauthorized access to download this submission file.')
        return redirect('leader_dashboard')

    file_full_path = get_submission_pdf_path(submission.pdf_path)

    if not os.path.exists(file_full_path):
        raise Http404("File not found on server")
    
    content_type, encoding = mimetypes.guess_type(file_full_path)
    if content_type is None:
        content_type = 'application/octet-stream'

    return FileResponse(
        open(file_full_path, 'rb'),
        as_attachment=True,
        filename=os.path.basename(file_full_path),
        content_type=content_type
    )
