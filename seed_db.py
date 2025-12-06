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
    """Create test users - all students created as 'student' role"""
    print("\nCreating users...")
    
    users = [
        ('lecturer@test.com', 'password123', 'lecturer'),
        ('student1@test.com', 'password123', 'student'),
        ('student2@test.com', 'password123', 'student'),
        ('student3@test.com', 'password123', 'student'),
        ('student4@test.com', 'password123', 'student'),
    ]
    
    created_users = {}
    for email, password, role in users:
        user = UserModel.create(email, password, role)
        if user:
            user_key = email.split('@')[0]
            created_users[user_key] = user
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
    """Create test groups - promotes creator to 'leader' role"""
    print("\nCreating groups...")
    
    ai_class = classes.get('Artificial Intelligence 101')
    student1 = users.get('student1')
    
    if not ai_class or not student1:
        print("✗ Class or student not found")
        return {}
    
    groups_data = [
        ('Group Alpha', 'alphapass'),
        ('Group Beta', 'betapass'),
    ]
    
    created_groups = {}
    for name, password in groups_data:
        group = GroupModel.create(
            str(ai_class.id),
            str(student1.id),
            name,
            password
        )
        if group:
            # Promote student to 'leader' role when they create a group
            UserModel.update_role(str(student1.id), 'leader')
            
            created_groups[name] = group
            print(f"✓ Created group: {name}")
            print(f"  Group ID: {group.id}")
            print(f"  Password: {password}")
            print(f"  Creator promoted to 'leader' role")
            
            # Add students to whitelist
            GroupModel.add_whitelist_email(str(group.id), 'student2@test.com')
            GroupModel.add_whitelist_email(str(group.id), 'student3@test.com')
            GroupModel.add_whitelist_email(str(group.id), 'student4@test.com')
            print(f"  Whitelisted: student2@test.com, student3@test.com, student4@test.com")
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
    """Add task divisions for students"""
    print("\nAdding task divisions...")
    
    task = tasks.get('Machine Learning Fundamentals')
    student2 = users.get('student2')
    student3 = users.get('student3')
    
    if not task or not student2 or not student3:
        print("✗ Task or students not found")
        return
    
    divisions = [
        (str(student2.id), 'Part 1: Explain supervised learning with 3 examples'),
        (str(student3.id), 'Part 2: Explain unsupervised learning with 3 examples'),
    ]
    
    for student_id, part_desc in divisions:
        TaskModel.add_division(str(task.id), student_id, part_desc)
        print(f"✓ Added division: {part_desc}")

def main():
    """Main seeding function"""
    print("="*60)
    print("CLASSROOM MANAGEMENT SYSTEM - DATABASE SEEDING")
    print("="*60)
    
    # Clear existing data
    clear_database()
    
    # Create test data
    users = create_users()
    classes = create_classes(users)
    groups = create_groups(classes, users)
    tasks = create_tasks(classes, users)
    add_task_divisions(tasks, users)
    
    print("\n" + "="*60)
    print("SEEDING COMPLETE!")
    print("="*60)
    print("\n📝 Test Accounts Created:")
    print("  Lecturer: lecturer@test.com / password123")
    print("  Student 1: student1@test.com / password123 (becomes Leader after creating group)")
    print("  Student 2: student2@test.com / password123")
    print("  Student 3: student3@test.com / password123")
    print("  Student 4: student4@test.com / password123")
    print("\n🔑 Class Credentials:")
    print("  Class 1: 'Artificial Intelligence 101' / 'ai101pass'")
    print("  Class 2: 'Web Development' / 'webdevpass'")
    print("\n✨ Role System:")
    print("  • All new users start as Students")
    print("  • Creating a group automatically promotes to Group Leader")
    print("  • Lecturer role is assigned by administrators only")

if __name__ == '__main__':
    main()
