from mongoengine import Document, StringField, EmailField, ListField, ReferenceField, DateTimeField, BooleanField, CASCADE
from datetime import datetime
import bcrypt

class UserModel(Document):
    """
    Represents a user in the system.
    Roles: 'lecturer', 'leader', 'member'
    """
    ROLE_LECTURER = 'lecturer'
    ROLE_LEADER = 'leader'
    ROLE_MEMBER = 'member'
    ROLES = [ROLE_LECTURER, ROLE_LEADER, ROLE_MEMBER]

    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True)
    role = StringField(choices=ROLES, default=ROLE_MEMBER)
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'users'}

    @classmethod
    def create(cls, email, password, role=ROLE_MEMBER):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user = cls(email=email, password_hash=hashed_password, role=role)
        user.save()
        return user

    @classmethod
    def authenticate(cls, email, password):
        user = cls.objects(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return user
        return None

    @classmethod
    def get_by_email(cls, email):
        return cls.objects(email=email).first()

    @classmethod
    def get_by_id(cls, user_id):
        return cls.objects(id=user_id).first()

    @classmethod
    def update_role(cls, user_id, new_role):
        user = cls.objects(id=user_id).first()
        if user:
            user.role = new_role
            user.save()
            return True
        return False

class ClassModel(Document):
    """
    Represents a class created by a lecturer.
    """
    name = StringField(required=True, unique=True)
    password_hash = StringField(required=True)
    lecturer = ReferenceField(UserModel, reverse_delete_rule=CASCADE)
    members = ListField(ReferenceField(UserModel))
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'classes'}

    @classmethod
    def create(cls, name, password, lecturer_id):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        class_obj = cls(name=name, password_hash=hashed_password, lecturer=lecturer_id)
        class_obj.save()
        return class_obj

    @classmethod
    def get_by_id(cls, class_id):
        return cls.objects(id=class_id).first()

    @classmethod
    def get_by_lecturer(cls, lecturer_id):
        return cls.objects(lecturer=lecturer_id).all()

    @classmethod
    def get_by_name(cls, name):
        return cls.objects(name=name).first()

    @classmethod
    def verify_password(cls, class_name, password):
        class_obj = cls.objects(name=class_name).first()
        if class_obj and bcrypt.checkpw(password.encode('utf-8'), class_obj.password_hash.encode('utf-8')):
            return True
        return False

    @classmethod
    def add_leader(cls, class_id, user_id):
        class_obj = cls.objects(id=class_id).first()
        user = UserModel.get_by_id(user_id)
        if class_obj and user:
            # Add user to the members list if not already there
            if user not in class_obj.members:
                class_obj.members.append(user)
                class_obj.save()
            return True
        return False

    @classmethod
    def get_by_member(cls, user_id):
        """Find classes a user is a member of."""
        return cls.objects(members=user_id).all()

class GroupModel(Document):
    """
    Represents a group within a class.
    """
    name = StringField(required=True)
    password_hash = StringField(required=True)
    class_obj = ReferenceField(ClassModel, required=True, reverse_delete_rule=CASCADE) # Added required=True
    leader = ReferenceField(UserModel, reverse_delete_rule=CASCADE)
    members = ListField(ReferenceField(UserModel))
    whitelist_emails = ListField(EmailField())
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'groups', 'indexes': [{'fields': ('name', 'class_obj'), 'unique': True}]}

    @classmethod
    def create(cls, class_obj, leader_id, name, password): # Changed class_id to class_obj
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        group = cls(name=name, password_hash=hashed_password, class_obj=class_obj, leader=leader_id, members=[leader_id])
        group.save()
        return group

    @classmethod
    def get_by_id(cls, group_id):
        return cls.objects(id=group_id).first()

    @classmethod
    def get_by_class(cls, class_id):
        return cls.objects(class_obj=class_id).all()

    @classmethod
    def get_by_leader(cls, leader_id):
        return cls.objects(leader=leader_id).all()

    @classmethod
    def get_by_member(cls, member_id):
        return cls.objects(members=member_id).all()

    @classmethod
    def verify_password(cls, group_id, password):
        group = cls.objects(id=group_id).first()
        if group and bcrypt.checkpw(password.encode('utf-8'), group.password_hash.encode('utf-8')):
            return True
        return False

    @classmethod
    def add_member(cls, group_id, member_id):
        group = cls.objects(id=group_id).first()
        member_user = UserModel.get_by_id(member_id)
        if group and member_user and member_user not in group.members:
            group.members.append(member_user)
            group.save()
            return True
        return False

    @classmethod
    def add_whitelist_email(cls, group_id, email):
        group = cls.objects(id=group_id).first()
        if group and email not in group.whitelist_emails:
            group.whitelist_emails.append(email)
            group.save()
            return True
        return False

    @classmethod
    def remove_whitelist_email(cls, group_id, email):
        group = cls.objects(id=group_id).first()
        if group and email in group.whitelist_emails:
            group.whitelist_emails.remove(email)
            group.save()
            return True
        return False


class TaskModel(Document):
    """
    Represents a task assigned to a class.
    """
    class_obj = ReferenceField(ClassModel, reverse_delete_rule=CASCADE)
    lecturer = ReferenceField(UserModel, reverse_delete_rule=CASCADE)
    title = StringField(required=True)
    description = StringField() # For text-based tasks
    file_path = StringField() # For file-based tasks
    due_date = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    divisions = ListField(dict())  # [{'member_id': '...', 'part_description': '...'}]

    meta = {'collection': 'tasks'}

    @classmethod
    def create(cls, class_id, lecturer_id, title, description=None, file_path=None, due_date=None):
        task = cls(
            class_obj=class_id,
            lecturer=lecturer_id,
            title=title,
            description=description,
            file_path=file_path,
            due_date=due_date
        )
        task.save()
        return task

    @classmethod
    def get_by_id(cls, task_id):
        return cls.objects(id=task_id).first()

    @classmethod
    def get_by_class(cls, class_id):
        return cls.objects(class_obj=class_id).all()

    @classmethod
    def add_division(cls, task_id, member_id, part_description):
        task = cls.objects(id=task_id).first()
        if task:
            # Remove existing division for this member if any
            task.divisions = [div for div in task.divisions if div.get('member_id') != member_id]
            task.divisions.append({'member_id': member_id, 'part_description': part_description})
            task.save()
            return True
        return False

class SubmissionModel(Document):
    """
    Represents a member's submission for a task.
    """
    task = ReferenceField(TaskModel, reverse_delete_rule=CASCADE)
    group = ReferenceField(GroupModel, reverse_delete_rule=CASCADE)
    member = ReferenceField(UserModel, reverse_delete_rule=CASCADE)
    text_answer = StringField()
    pdf_path = StringField() # Relative path to the generated PDF
    submitted_at = DateTimeField(default=datetime.utcnow)
    status = StringField(default='submitted') # e.g., 'submitted', 'graded'

    meta = {'collection': 'submissions'}

    @classmethod
    def create(cls, task_id, group_id, member_id, text_answer, pdf_path):
        submission = cls(task=task_id, group=group_id, member=member_id,
                         text_answer=text_answer, pdf_path=pdf_path)
        submission.save()
        return submission

    @classmethod
    def get_by_task_and_member(cls, task_id, member_id):
        return cls.objects(task=task_id, member=member_id).first()

    @classmethod
    def get_by_task_and_group(cls, task_id, group_id):
        return cls.objects(task=task_id, group=group_id).all()

class CompiledSubmissionModel(Document):
    """
    Represents a compiled group submission (e.g., merged PDFs).
    """
    group = ReferenceField(GroupModel, reverse_delete_rule=CASCADE)
    task = ReferenceField(TaskModel, reverse_delete_rule=CASCADE)
    compiled_pdf_path = StringField() # Relative path to the compiled PDF
    compiled_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'compiled_submissions'}

    @classmethod
    def create(cls, group_id, task_id, compiled_pdf_path):
        compiled_sub = cls(group=group_id, task=task_id, compiled_pdf_path=compiled_pdf_path)
        compiled_sub.save()
        return compiled_sub

    @classmethod
    def get_by_task_and_group(cls, task_id, group_id):
        return cls.objects(task=task_id, group=group_id).first()

    @classmethod
    def get_by_task(cls, task_id):
        return cls.objects(task=task_id).all()
