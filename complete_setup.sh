#!/bin/bash

# Complete Setup Script for Classroom Management System
# Run this after copying all files to your project directory

set -e  # Exit on error

echo "=================================================="
echo "  Classroom Management System - Complete Setup"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}This script is designed for Linux systems${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mongodb
sudo apt install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

echo -e "${GREEN}✓ System dependencies installed${NC}"
echo ""

echo -e "${YELLOW}Step 2: Starting MongoDB...${NC}"
sudo systemctl start mongodb
sudo systemctl enable mongodb
if sudo systemctl is-active --quiet mongodb; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo -e "${RED}✗ MongoDB failed to start${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}Step 3: Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists${NC}"
fi
echo ""

echo -e "${YELLOW}Step 4: Activating virtual environment and installing packages...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Python packages installed${NC}"
echo ""

echo -e "${YELLOW}Step 5: Creating directory structure...${NC}"
mkdir -p media/submissions
mkdir -p media/compiled
mkdir -p static
mkdir -p templates/lecturer
mkdir -p templates/leader
mkdir -p templates/member
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo -e "${YELLOW}Step 6: Setting up .env file...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from template${NC}"
    echo -e "${YELLOW}⚠ Please edit .env file with your settings!${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi
echo ""

echo -e "${YELLOW}Step 7: Creating Django project structure...${NC}"
if [ ! -f "manage.py" ]; then
    django-admin startproject classroom_manager .
    echo -e "${GREEN}✓ Django project created${NC}"
else
    echo -e "${YELLOW}Django project already exists${NC}"
fi

if [ ! -d "core" ]; then
    python manage.py startapp core
    echo -e "${GREEN}✓ Core app created${NC}"
else
    echo -e "${YELLOW}Core app already exists${NC}"
fi
echo ""

echo -e "${YELLOW}Step 8: Running Django migrations...${NC}"
python manage.py migrate
echo -e "${GREEN}✓ Database migrations complete${NC}"
echo ""

echo -e "${YELLOW}Step 9: Creating remaining templates...${NC}"

# Create submit_task.html
cat > templates/member/submit_task.html << 'TEMPLATE_EOF'
{% extends 'base.html' %}
{% block title %}Submit Task{% endblock %}
{% block content %}
<div class="mb-6">
    <h1 class="text-3xl font-bold">{{ task.title }}</h1>
    <p class="text-gray-600 mt-2">{{ task.description }}</p>
</div>
{% if member_part %}
<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
    <h2 class="font-bold text-blue-900 mb-2">Your Assigned Part:</h2>
    <p class="text-blue-800">{{ member_part }}</p>
</div>
{% endif %}
<div class="bg-white rounded-lg shadow-md p-8">
    <form method="post">
        {% csrf_token %}
        <div class="mb-6">
            <label class="block text-sm font-medium mb-2">Your Answer</label>
            {{ form.text_answer }}
            <p class="text-sm text-gray-500 mt-2">Your text will be automatically converted to PDF</p>
        </div>
        {% if existing_submission %}
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <p class="text-yellow-800"><strong>Note:</strong> Submitting again will replace your previous submission.</p>
        </div>
        {% endif %}
        <button type="submit" class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg">Submit Answer</button>
    </form>
</div>
{% endblock %}
TEMPLATE_EOF

# Create create_task.html
cat > templates/lecturer/create_task.html << 'TEMPLATE_EOF'
{% extends 'base.html' %}
{% block title %}Create Task{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Create New Task for {{ class_obj.name }}</h1>
    <div class="bg-white rounded-lg shadow-md p-8">
        <form method="post">
            {% csrf_token %}
            <div class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2">Task Title</label>
                    {{ form.title }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Description</label>
                    {{ form.description }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Due Date (Optional)</label>
                    {{ form.due_date }}
                </div>
                <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg">Create Task</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

# Create view_submissions.html
cat > templates/lecturer/view_submissions.html << 'TEMPLATE_EOF'
{% extends 'base.html' %}
{% block title %}View Submissions{% endblock %}
{% block content %}
<div class="mb-6">
    <h1 class="text-3xl font-bold">{{ task.title }} - Submissions</h1>
    <p class="text-gray-600 mt-2">{{ task.description }}</p>
</div>
<div class="space-y-4">
    {% for group in groups %}
    <div class="bg-white rounded-lg shadow-md p-6">
        <div class="flex justify-between items-center">
            <div>
                <h3 class="text-xl font-bold">{{ group.name }}</h3>
                <p class="text-gray-600">Members: {{ group.members|length }}</p>
            </div>
            {% with group.id|stringformat:"s" as group_id_str %}
                {% if submission_map|get_item:group_id_str %}
                <a href="{% url 'download_compiled' group.id task.id %}" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg">Download PDF</a>
                {% else %}
                <span class="text-gray-500">Not submitted</span>
                {% endif %}
            {% endwith %}
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
TEMPLATE_EOF

# Create group_detail.html
cat > templates/leader/group_detail.html << 'TEMPLATE_EOF'
{% extends 'base.html' %}
{% block title %}{{ group.name }}{% endblock %}
{% block content %}
<div class="mb-6">
    <h1 class="text-3xl font-bold">{{ group.name }}</h1>
    <p class="text-gray-600">Class: {{ class_obj.name }}</p>
    <p class="text-sm text-gray-500">Group ID: {{ group.id }}</p>
</div>
<div class="bg-white rounded-lg shadow-md p-6 mb-6">
    <h2 class="text-2xl font-bold mb-4">Whitelist Management</h2>
    <form method="post" action="{% url 'add_whitelist' group.id %}" class="mb-4">
        {% csrf_token %}
        <div class="flex gap-2">
            <input type="email" name="email" placeholder="member@example.com" required class="flex-1 px-4 py-2 border border-gray-300 rounded-lg">
            <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg">Add Email</button>
        </div>
    </form>
    <div class="space-y-2">
        {% for email in group.whitelist_emails %}
        <div class="flex justify-between items-center bg-gray-50 p-3 rounded">
            <span>{{ email }}</span>
            <a href="{% url 'remove_whitelist' group.id email %}" class="text-red-600 hover:text-red-700">Remove</a>
        </div>
        {% endfor %}
    </div>
</div>
<div class="bg-white rounded-lg shadow-md p-6 mb-6">
    <h2 class="text-2xl font-bold mb-4">Members ({{ members|length }})</h2>
    <div class="space-y-2">
        {% for member in members %}
        <div class="bg-gray-50 p-3 rounded">
            {{ member.email }}
            {% if member.id|stringformat:"s" == group.leader_id %}
            <span class="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Leader</span>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</div>
<div class="bg-white rounded-lg shadow-md p-6">
    <h2 class="text-2xl font-bold mb-4">Tasks</h2>
    <div class="space-y-4">
        {% for task in tasks %}
        <div class="border border-gray-200 rounded-lg p-4">
            <h3 class="text-lg font-bold">{{ task.title }}</h3>
            <p class="text-gray-600 mt-1">{{ task.description|truncatewords:15 }}</p>
            <div class="mt-4 flex gap-2">
                <a href="{% url 'divide_task' group.id task.id %}" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">Divide Task</a>
                <a href="{% url 'compile_submission' group.id task.id %}" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm">Compile Submissions</a>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

# Create create_group.html
cat > templates/leader/create_group.html << 'TEMPLATE_EOF'
{% extends 'base.html' %}
{% block title %}Create Group{% endblock %}
{% block content %}
<div class="max-w-2xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">Create Group for {{ class_obj.name }}</h1>
    <div class="bg-white rounded-lg shadow-md p-8">
        <form method="post">
            {% csrf_token %}
            <div class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2">Group Name</label>
                    {{ form.name }}
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Group Password</label>
                    {{ form.password }}
                    <p class="text-sm text-gray-500 mt-1">Share this with whitelisted members</p>
                </div>
                <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg">Create Group</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
TEMPLATE_EOF

# Create divide_task.html
cat > templates/leader/divide_task.html << 'TEMPLATE_EOF'
{% extends 'base.html' %}
{% block title %}Divide Task{% endblock %}
{% block content %}
<div class="mb-6">
    <h1 class="text-3xl font-bold">Divide Task: {{ task.title }}</h1>
    <p class="text-gray-600 mt-2">{{ group.name }}</p>
</div>
<div class="bg-white rounded-lg shadow-md p-8">
    <form method="post">
        {% csrf_token %}
        <div class="space-y-6">
            {% for member in members %}
            <div class="border border-gray-200 rounded-lg p-4">
                <label class="block text-sm font-semibold mb-2">{{ member.email }}</label>
                <textarea name="part_{{ member.id }}" rows="3" class="w-full px-4 py-2 border border-gray-300 rounded-lg" placeholder="Describe what this member should work on..."></textarea>
            </div>
            {% endfor %}
        </div>
        <button type="submit" class="mt-6 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg">Save Task Divisions</button>
    </form>
</div>
{% endblock %}
TEMPLATE_EOF

echo -e "${GREEN}✓ All templates created${NC}"
echo ""

echo -e "${YELLOW}Step 10: Setting proper permissions...${NC}"
chmod -R 755 media/
chmod +x seed_db.py
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

echo -e "${YELLOW}Step 11: Seeding database with test data...${NC}"
python seed_db.py
echo ""

echo "=================================================="
echo -e "${GREEN}  ✓ Setup Complete!${NC}"
echo "=================================================="
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Review .env file and adjust settings if needed"
echo "2. Run: ${YELLOW}source venv/bin/activate${NC}"
echo "3. Run: ${YELLOW}python manage.py runserver${NC}"
echo "4. Open browser: ${YELLOW}http://127.0.0.1:8000${NC}"
echo ""
echo -e "${GREEN}Test Accounts:${NC}"
echo "Lecturer: lecturer@test.com / password123"
echo "Leader:   leader@test.com / password123"
echo "Member:   member1@test.com / password123"
echo ""
echo "=================================================="