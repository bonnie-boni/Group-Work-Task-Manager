#!/usr/bin/env python
"""
Database Seeding Script for Classroom Management System
Creates test users, classes, groups, and tasks
"""
import os
import sys
import django
from datetime import datetime, timedelta, UTC

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classroom_manager.settings')
django.setup()

from core.models import UserModel, ClassModel, GroupModel, TaskModel
from core.db import get_db

def clear_database():
    """Clear all collections"""
    print("Clearing database...")
    db = get_db()
    collections = ['users', 'classes', 'groups', 'tasks', 'submissions', 'compiled_submissions']
    for collection in collections:
        db[collection].delete_many({})
    print("Database cleared!")

def create_users():
    """Create test users"""
    print("\nCreating users...")
    
    users = [
        ('lecturer@test.com', 'password123', 'lecturer'),
        ('leader@test.com', 'password123', 'leader'),
        ('member1@test.com', 'password123', 'member'),
        ('member2@test.com', 'password123', 'member'),
        ('member3@test.com', 'password123', 'member'),
    ]
    
    created_users = {}
    for email, password, role in users:
        user = UserModel.create(email, password, role)
        if user:
            created_users[role + ('_' + email.split('@')[0] if role == 'member' else '')] = user
            print(f"✓ Created {role}: {email}")
        else:
            print(f"✗ Failed to create {email}")
    
    return created_users

def create_classes(users):
    """Create test classes"""
    print("\nCreating classes...")
    
    lecturer = users.get('lecturer')
    if not lecturer:
        print("✗ Lecturer not found")
        return {}
    
    classes = [
        ('Artificial Intelligence 101', 'ai101pass'),
        ('Web Development', 'webdevpass'),
    ]
    
    created_classes = {}
    for name, password in classes:
        class_obj = ClassModel.create(name, password, str(lecturer.id))
        if class_obj:
            created_classes[name] = class_obj
            print(f"✓ Created class: {name}")
            print(f"  Class ID: {class_obj.id}")
            print(f"  Password: {password}")
        else:
            print(f"✗ Failed to create class {name}")
    
    return created_classes

def create_groups(classes, users):
    """Create test groups"""
    print("\nCreating groups...")
    
    ai_class = classes.get('Artificial Intelligence 101')
    leader = users.get('leader')
    
    if not ai_class or not leader:
        print("✗ Class or leader not found")
        return {}
    
    groups_data = [
        ('Group Alpha', 'alphap ass'),
        ('Group Beta', 'betapass'),
    ]
    
    created_groups = {}
    for name, password in groups_data:
        group = GroupModel.create(
            str(ai_class.id),
            str(leader.id),
            name,
            password
        )
        if group:
            created_groups[name] = group
            print(f"✓ Created group: {name}")
            print(f"  Group ID: {group.id}")
            print(f"  Password: {password}")
            
            # Add members to whitelist
            GroupModel.add_whitelist_email(str(group.id), 'member1@test.com')
            GroupModel.add_whitelist_email(str(group.id), 'member2@test.com')
            GroupModel.add_whitelist_email(str(group.id), 'member3@test.com')
            print(f"  Whitelisted: member1@test.com, member2@test.com, member3@test.com")
        else:
            print(f"✗ Failed to create group {name}")
    
    return created_groups

def create_tasks(classes, users):
    """Create test tasks"""
    print("\nCreating tasks...")
    
    ai_class = classes.get('Artificial Intelligence 101')
    lecturer = users.get('lecturer')
    
    if not ai_class or not lecturer:
        print("✗ Class or lecturer not found")
        return {}
    
    tasks_data = [
        (
            'Machine Learning Fundamentals',
            'Write a comprehensive report on supervised vs unsupervised learning. Include examples and applications.',
            datetime.now(UTC) + timedelta(days=7)
        ),
        (
            'Neural Networks Research',
            'Research and explain the architecture of Convolutional Neural Networks. Include diagrams and use cases.',
            datetime.now(UTC) + timedelta(days=14)
        ),
        (
            'AI Ethics Essay',
            'Discuss the ethical implications of artificial intelligence in society. Cover bias, privacy, and accountability.',
            datetime.now(UTC) + timedelta(days=21)
        ),
    ]
    
    created_tasks = {}
    for title, description, due_date in tasks_data:
        task = TaskModel.create(
            class_id=str(ai_class.id),
            lecturer_id=str(lecturer.id),
            title=title,
            description=description,
            due_date=due_date
        )
        if task:
            created_tasks[title] = task
            print(f"✓ Created task: {title}")
            print(f"  Task ID: {task.id}")
            print(f"  Due: {due_date.strftime('%Y-%m-%d')}")
        else:
            print(f"✗ Failed to create task {title}")
    
    return created_tasks

def add_task_divisions(tasks, users):
    """Add task divisions for members"""
    print("\nAdding task divisions...")
    
    task = tasks.get('Machine Learning Fundamentals')
    member1 = users.get('member_member1')
    member2 = users.get('member_member2')
    
    if not task or not member1 or not member2:
        print("✗ Task or members not found")
        return
    
    divisions = [
        (str(member1.id), 'Part 1: Explain supervised learning with 3 examples'),
        (str(member2.id), 'Part 2: Explain unsupervised learning with 3 examples'),
    ]
    
    for member_id, part_desc in divisions:
        TaskModel.add_division(str(task.id), member_id, part_desc)
        print(f"✓ Added division: {part_desc}")

def main():
    """Main seeding function"""
    print("="*60)
    print("CLASSROOM MANAGEMENT SYSTEM - DATABASE SEEDING")
    print("="*60)
    
    # Clear existing data
    clear_database()
    
    # # Create test data (commented out to prevent creation of test accounts)
    # users = create_users()
    # classes = create_classes(users)
    # groups = create_groups(classes, users)
    # tasks = create_tasks(classes, users)
    # add_task_divisions(tasks, users)
    
    # # Print summary (commented out as no test data is created)
    # print_summary(users, classes, groups, tasks)

if __name__ == '__main__':
    main()
