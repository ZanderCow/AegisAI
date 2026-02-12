-- BACKEND --

Prerequisites:
  - Python 3.10+
  - Docker Desktop (for PostgreSQL database)
  - pip (Python package manager)


1. Navigate to the backend directory:

   cd backend


2. Create and activate a virtual environment:

   python -m venv .venv

   macOS / Linux:
     source .venv/bin/activate

   Windows:
     .venv\Scripts\activate


3. Install dependencies:

   pip install -r requirements.txt


4. Spin up the PostgreSQL database with Docker:

   From the project root:

   docker build -t aegisai-db ./database
   docker run -d --name aegisai-postgres -p 5432:5432 aegisai-db

   ** NOTE: Make sure Docker Desktop is running before executing these commands.
   ** NOTE: The container uses these defaults (set in database/dockerfile):
              User:     aegis_user
              Password: aegis_pass
              Database: aegisai
            These match the DATABASE_URL in backend/.env.


5. Run the backend server:

   cd backend
   uvicorn src.main:app --reload

   ** NOTE: The --reload flag causes the server to auto-restart when you
            edit code in the backend. This is for development only.

   The API will be available at http://127.0.0.1:8000
   Interactive docs are at http://127.0.0.1:8000/docs