-- BACKEND --

cd into the backend directory


run the commands:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt


Server is now ready to be ran. To do this, run the following:
uvicorn main:app --reload

  ** NOTE: The --reload flag causes the server to update when you edit code in the backend


-- FRONTEND --


-- DATABASE (Test Container) --

Prerequisites: Docker must be installed and running.

1. Build the image (run from the project root):
   docker build -f db/Dockerfile.test -t aegisai-db-test db/

2. Start the container:
   docker run -d --name aegisai-db-test-container -p 5433:5432 aegisai-db-test

   This exposes Postgres on localhost port 5433 (so it doesn't clash with a local Postgres on 5432).

3. Connect with psql to verify it's running:
   docker exec -it aegisai-db-test-container psql -U test_admin -d aegis_test_db

   Or connect from the host if you have psql installed:
   psql -h localhost -p 5433 -U test_admin -d aegis_test_db

   Connection details:
     Host:     localhost
     Port:     5433
     Database: aegis_test_db
     User:     test_admin
     Password: test_password

4. Verify the schema was applied:
   \dt                   -- should list the 'users' table
   SELECT * FROM users;  -- should return an empty table

5. Stop and remove the container when done:
   docker rm -f aegisai-db-test-container

