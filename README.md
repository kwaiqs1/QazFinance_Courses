# QazFinance Academy (Django)

This project is a Stepik/Coursera-style learning platform:
- Courses → Units → Lessons
- Lesson structure: Topic → Objectives → Theory → Practice (quiz) → Case → Summary
- Quizzes: 3 choices, 1 correct
- Progress per lesson (best & last score) + completion status
- Profile rating = average best score across all lessons attempted
- Registration with email verification (Gmail App Password supported)
- People search like LinkedIn (public profile pages)

## Quickstart (Windows / PyCharm)

### 1) Create venv & install deps
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Create `.env`
Copy `.env.example` to `.env` and set `SECRET_KEY`.
Optionally configure Gmail App Password SMTP (or keep console email backend for local dev).

### 3) Migrations & admin
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open:
- http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Content entry workflow (Admin)
1. Create Course
2. Add Units
3. Add Lessons to Units
4. Add Questions and Choices to each Lesson (ensure exactly 1 correct choice)

## Notes on rich content
Lesson fields accept **basic HTML** (entered by admin). This is rendered with `|safe` in templates.
Only trusted admins should enter content.
