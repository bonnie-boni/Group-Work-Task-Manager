"""
URL Configuration for Core App
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Lecturer URLs
    path('lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/create-class/', views.create_class, name='create_class'),
    path('lecturer/class/<str:class_name>/', views.class_detail, name='class_detail'),
    path('lecturer/class/<str:class_name>/create-task/', views.create_task, name='create_task'),
    path('lecturer/task/<str:task_id>/submissions/', views.view_submissions, name='view_submissions'),
    
    # Leader URLs
    path('leader/', views.leader_dashboard, name='leader_dashboard'),
    path('leader/join-class/', views.join_class_view, name='join_class'),
    path('leader/create-group/', views.create_group, name='create_group'),
    path('leader/group/<str:group_id>/', views.group_detail, name='group_detail'),
    path('leader/group/<str:group_id>/add-whitelist/', views.add_whitelist, name='add_whitelist'),
    path('leader/group/<str:group_id>/remove-whitelist/<str:email>/', views.remove_whitelist, name='remove_whitelist'),
    path('leader/group/<str:group_id>/task/<str:task_id>/divide/', views.divide_task, name='divide_task'),
    path('leader/group/<str:group_id>/task/<str:task_id>/submissions/', views.leader_view_submissions, name='leader_view_submissions'),
    path('leader/group/<str:group_id>/task/<str:task_id>/send-compiled/', views.leader_send_compiled_work, name='leader_send_compiled_work'),
    
    # Download URLs (placed early to avoid conflicts)
    path('download/compiled/<str:group_id>/<str:task_id>/', views.download_compiled, name='download_compiled'),
    path('download/task/<str:task_id>/', views.download_task_file, name='download_task_file'),
    
    # Member URLs
    path('member/', views.member_dashboard, name='member_dashboard'),
    path('member/group/<str:group_id>/accept-invitation/', views.accept_group_invitation, name='accept_group_invitation'),
    path('member/task/<str:task_id>/submit/', views.submit_task, name='submit_task'),
    
    # Polling API
    path('api/poll/tasks/<str:class_name>/', views.poll_tasks, name='poll_tasks'),
    path('api/poll/submissions/<str:task_id>/<str:group_id>/', views.poll_submissions, name='poll_submissions'),
]
