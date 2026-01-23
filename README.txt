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

