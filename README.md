# Classroom Management System

A Django + MongoDB web application for managing classroom tasks, groups, and submissions with role-based access control.

## Features

- **Three Role System**: Lecturer, Group Leader, and Member
- **Session-Based Authentication**: 2-hour session expiry
- **PDF Generation**: Automatic PDF creation from text submissions (WeasyPrint/ReportLab)
- **Group Management**: Leaders can create groups, whitelist members, and compile submissions
- **Task Division**: Leaders divide tasks among group members
- **Polling Updates**: Real-time updates via JavaScript polling (15s interval)

## System Requirements

- Linux Mint (or Ubuntu-based)
- Python 3.10+
- MongoDB 4.4+
- System libraries for WeasyPrint

## Installation

### 1. Clone and Setup

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup (installs dependencies and creates structure)
./setup.sh
```

### 2. Configure Environment

```bash
# Copy and edit .env file
cp .env.example .env
nano .env
```

Edit `.env` with your configuration:
- Set a strong `SECRET_KEY`
- Configure MongoDB connection
- Adjust session settings if needed

### 3. Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Create Django migrations
python manage.py migrate

# Seed database with test data
python seed_db.py
```

### 4. Run Development Server

```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000`

## Test Accounts

After running `seed_db.py`:

| Role | Email | Password |
|------|-------|----------|
| Lecturer | lecturer@test.com | password123 |
| Leader | leader@test.com | password123 |
| Member | member1@test.com | password123 |
| Member | member2@test.com | password123 |

## Project Structure

```
classroom_manager/
├── classroom_manager/        # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                     # Main application
│   ├── db.py                # MongoDB connection
│   ├── models.py            # Data access layer
│   ├── views.py             # View controllers
│   ├── forms.py             # Django forms
│   ├── decorators.py        # Access control decorators
│   ├── middleware.py        # Custom middleware
│   ├── context_processors.py
│   ├── pdf_utils.py         # PDF generation utilities
│   └── urls.py              # URL routing
├── templates/               # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── lecturer/
│   ├── leader/
│   └── member/
├── media/                   # Uploaded files
│   ├── submissions/         # Individual PDFs
│   └── compiled/            # Compiled group PDFs
├── static/                  # Static files (CSS/JS)
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── setup.sh                 # Setup script
└── seed_db.py              # Database seeding script
```

## User Workflows

### Lecturer Workflow

1. Login with lecturer account
2. Create a class (get Class ID and password)
3. Share Class ID and password with students
4. Create tasks for the class
5. View group submissions
6. Download compiled group PDFs

### Group Leader Workflow

1. Register/Login (role = member initially)
2. Join a class using Class ID and password
3. Create a group (role auto-upgrades to leader)
4. Add member emails to whitelist
5. Share Group ID and password with whitelisted members
6. Divide tasks among group members
7. Compile member submissions into group PDF
8. Submit compiled PDF to lecturer

### Member Workflow

1. Register/Login
2. Get Group ID and password from leader
3. Verify email is whitelisted
4. Join group
5. View assigned task portions
6. Submit text answers (auto-converts to PDF)
7. Leader compiles all member PDFs

## API Endpoints

### Polling Endpoints

```javascript
// Poll for task updates (every 15 seconds)
GET /api/poll/tasks/<class_id>/

// Poll for submission updates
GET /api/poll/submissions/<task_id>/<group_id>/
```

### Example Polling Implementation

```javascript
// Add this to your templates
<script>
// Poll for task updates
setInterval(() => {
    fetch('/api/poll/tasks/{{ class_obj.id }}/')
        .then(res => res.json())
        .then(data => {
            // Update task list in DOM
            console.log('Tasks updated:', data.tasks);
        });
}, 15000);
</script>
```

## Database Collections

### users
- `_id`: ObjectId
- `email`: String (unique)
- `password_hash`: String
- `role`: String (lecturer|leader|member|admin)
- `whitelisted_groups`: Array[String]
- `created_at`: DateTime

### classes
- `_id`: ObjectId
- `name`: String
- `password_hash`: String
- `lecturer_id`: String
- `groups`: Array[String]
- `tasks`: Array[String]

### groups
- `_id`: ObjectId
- `class_id`: String
- `leader_id`: String
- `name`: String
- `password_hash`: String
- `members`: Array[String]
- `whitelist_emails`: Array[String]

### tasks
- `_id`: ObjectId
- `class_id`: String
- `lecturer_id`: String
- `title`: String
- `description`: String
- `due_date`: DateTime
- `divisions`: Array[{member_id, part_description}]

### submissions
- `_id`: ObjectId
- `task_id`: String
- `group_id`: String
- `member_id`: String
- `text_answer`: String
- `pdf_path`: String
- `submitted_at`: DateTime
- `status`: String

### compiled_submissions
- `_id`: ObjectId
- `group_id`: String
- `task_id`: String
- `compiled_pdf_path`: String
- `compiled_at`: DateTime

## Security Features

- PBKDF2 password hashing (Django default)
- CSRF protection on all forms
- Session-based authentication (2-hour expiry)
- Role-based access control via decorators
- Input validation and sanitization
- Rate limiting on login/register (django-ratelimit)

## PDF Generation

### Individual Member PDFs

When a member submits text:
1. Text is validated and sanitized
2. PDF is generated using WeasyPrint (preferred) or ReportLab (fallback)
3. PDF includes: task title, member email, submission date, content
4. File is saved to `media/submissions/`
5. Path is stored in database

### Group Compilation

When leader compiles submissions:
1. All member PDFs are retrieved
2. PDFs are merged using PyPDF2
3. Compiled PDF is saved to `media/compiled/`
4. Lecturer can download the final PDF

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB status
sudo systemctl status mongodb

# Start MongoDB
sudo systemctl start mongodb

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

### WeasyPrint Installation Issues

```bash
# Install system dependencies
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Reinstall WeasyPrint
pip uninstall weasyprint
pip install weasyprint
```

### Permission Issues

```bash
# Fix media directory permissions
chmod -R 755 media/
chown -R $USER:$USER media/
```

## Development

### Running Tests

```bash
python manage.py test core
```

### Creating Admin User

To manually assign lecturer role:

```python
from core.models import UserModel
from bson.objectid import ObjectId

# Get user
user = UserModel.get_by_email('user@example.com')

# Update to lecturer
UserModel.update_role(str(user['_id']), 'lecturer')
```

### Clearing Database

```bash
mongo
use classroom_db
db.dropDatabase()
```

Then re-run `python seed_db.py`

## Production Deployment

### Environment Variables

Set these in production `.env`:

```bash
DEBUG=False
SECRET_KEY=<generate-strong-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### HTTPS Configuration

Ensure you're using HTTPS in production for secure cookie transmission.

### Static Files

```bash
python manage.py collectstatic
```

Configure your web server (nginx/Apache) to serve static files.

## Support

For issues or questions:
1. Check MongoDB and Django logs
2. Verify environment variables in `.env`
3. Ensure all dependencies are installed
4. Check file permissions for media directories

## License

MIT License - Educational project for classroom management.