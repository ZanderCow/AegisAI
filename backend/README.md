# Backend Project

## Description
A Python backend application.

## Setup

### Prerequisites
- Python 3.11+
- Docker (optional)

### Local Development

1. Create and activate virtual environment:
```bash
source venv/bin/activate  # On Unix/macOS
# or
venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

### Docker

1. Build the Docker image:
```bash
docker build -t backend-app .
```

2. Run the container:
```bash
docker run -p 8000:8000 backend-app
```

## Project Structure
```
.
├── Dockerfile
├── README.md
├── requirements.txt
├── venv/
└── main.py
```

## Environment Variables
Configure your environment variables in a `.env` file (not tracked in git).

## License
MIT
