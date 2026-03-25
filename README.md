# Alumni Connect - Backend API

A robust FastAPI backend for the **Alumni Connect** platform, designed to bridge the gap between institutions and their alumni. This API handles user authentication, profile management, job postings, and event registrations.

## 🚀 Tech Stack
- **Framework:** FastAPI (Python 3.14+)
- **Database:** PostgreSQL (Hosted on Supabase)
- **Migrations:** Alembic
- **Deployment:** Render
- **Authentication:** OAuth2 with JWT (JSON Web Tokens)

## 📁 Project Structure
```text
├── app/
│   ├── db/                 # Database connection & session
│   ├── models/             # SQLAlchemy database models
│   ├── schemas/            # Pydantic data validation models
│   ├── api/             # API endpoints (Alumni, Jobs, Events)
│   └── main.py
|   |__core/            
├── alembic/                # Database migration scripts
├── alembic.ini             # Alembic configuration
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
