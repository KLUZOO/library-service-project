# 📚 Library Service Project

**Library Service Project** is a REST API service for managing a library system. It automates book lending, returns,
user management, and sends notifications to administrators. This project is part of the GoIT Flex program and serves as
practice for a complex technical assessment.

## 🚀 Project Goal

To replace the outdated manual library tracking system with an online platform that:

- Manages book inventory
- Automates borrowings and returns
- Sends notifications via Telegram Bot
- Provides a browsable API interface (no frontend implemented)

---

## 📂 Core Features

- **Books Service** — CRUD operations for books and inventory management.
- **Users Service** — User registration, authentication (JWT), and profile management.
- **Borrowings Service** — Create, view, and return borrowings with filtering.
- **Notifications Service** — Send Telegram notifications about new borrowings, overdue returns, and successful
  payments.
- Django Admin panel for managing resources.

---

## 🛠 Technology Stack

- **Backend:** Python, Django, Django REST Framework
- **Database:** sqlite3
- **Task Queue:** Celery + Redis
- **Notifications:** Telegram Bot API
- **Documentation:** DRF Spectacular (Swagger/OpenAPI)
- **Testing:** pytest, coverage (60%+ coverage)
- **Other:** docker-compose, python-dotenv for environment variables

---

## 📌 Models and Resources

### Book

| Field     | Type         | Description                |
|-----------|--------------|----------------------------|
| title     | string       | Book title                 |
| author    | string       | Author name                |
| cover     | Enum         | HARD or SOFT cover type    |
| inventory | positive int | Number of available copies |
| daily_fee | decimal      | Daily rental fee in USD    |

### User

| Field      | Type    | Description      |
|------------|---------|------------------|
| email      | string  | Unique email     |
| first_name | string  | First name       |
| last_name  | string  | Last name        |
| password   | string  | Password         |
| is_staff   | boolean | Admin privileges |

### Borrowing

| Field                | Type    | Description                |
|----------------------|---------|----------------------------|
| borrow_date          | date    | Date the book was borrowed |
| expected_return_date | date    | Expected return date       |
| actual_return_date   | date    | Actual return date         |
| book_id              | integer | Related book ID            |
| user_id              | integer | Related user ID            |

---

## 🔗 API Endpoints

### Books Service

- POST /api/books/ # Add new book (admin only)
- GET /api/books/ # List all books
- GET /api/books/{id}/ # Get book details
- PUT /api/books/{id}/ # Update book (admin only)
- DELETE /api/books/{id}/ # Delete book (admin only)

### Users Service

- POST /api/users/ # Register new user
- POST /api/users/token/ # Obtain JWT token
- POST /api/users/token/refresh/ # Refresh JWT token
- GET /api/users/me/ # Get own profile
- PUT /api/users/me/ # Update own profile

### Borrowings Service

- POST /api/borrowings/ # Create a borrowing (decrease book inventory by 1)
- GET /api/borrowings/ # List borrowings (filters: user_id, is_active)
- GET /api/borrowings/{id}/ # Get borrowing details
- POST /api/borrowings/{id}/return/ # Return book (increase inventory by 1)

---

## 📢 Notifications

Telegram notifications are sent to the library admin chat:

- When a new borrowing is created
- When a borrowing is overdue

---

## 🐳 Getting Started

1. Clone the repository

```
git clone https://github.com/KLUZOO/library-service-project.git
cd library-service
```

2. If you are using PyCharm - it may propose you to automatically create venv for your project and install requirements in it, but if not:

```
python -m venv venv
venv\Scripts\activate (on Windows)
source venv/bin/activate (on macOS)
pip install -r requirements.txt
```

3. Create .env file

   Copy .env.sample to .env and fill in the required environment variables:

```
cp .env.sample .env
```

4. Make migrations

```
python manage.py migrate
```

5. Run celery

```
docker run --name my-redis -p 6379:6379 -d redis
celery -A library_service worker --loglevel=info --pool=solo
celery -A library_service beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

6. Run django project

```
python manage.py runserver
```

