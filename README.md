# CarClinch Background Removal API

This project provides a background removal and background replacement application for car images.  
The project includes:

- a FastAPI backend
- a Flask frontend
- single-model background replacement support for local development

## Current Frontend Status

The frontend currently supports:

- uploading a car image
- uploading a background image
- processing with the single-model option
- previewing uploaded images
- displaying the processed result
- clearing the form and resetting the UI

At the moment, the project is configured for **single-model mode only** in the frontend.

---

## Local Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd carclinch-bg-removal-api
```

### 2. Create a virtual environment

```
python -m venv .venv
```

### 3. Activate the virtual environment

#### Windows PowerShell

```
.\.venv\Scripts\activate
```

#### macOS / Linux

```
source .venv/bin/activate
```

### 4. Install dependencies

```
python -m pip install -r api/src/requirements.txt
```

---

## Running the Project Locally

You need to run the backend and frontend in **separate terminals.**

### Terminal 1: Run the FastAPI backend

Activate the virtual environment first:

```
.\.venv\Scripts\activate
```

Then run:

```
python -m uvicorn main:app --reload --port 8000 --app-dir api/src
```

The backend should run at:

```
http://127.0.0.1:8000
```

### Terminal 2: Run the Flask frontend

Activate the virtual environment first:

```
.\.venv\Scripts\activate
```

Than run:

```
python frontend/app.py
```

The frontend should run at:

```
http://127.0.0.1:5000
```

---

## How to Use

1. Open the frontend in your browser:

```
http://127.0.0.1:5000
```

2. Upload:
   - a car image
   - a background image
3. Click Process Images
4. View the processed result
5. Use Clear Form to reset the form and previews

### Notes for Team Members

If you pull this branch to your own computer, the project will not run automatically until you install the dependencies in your local virtual environment.

Each team member must do the following after pulling the branch:

```
python -m venv .venv
```

Activate it:

```
.\.venv\Scripts\activate
```

Then install dependencies:

```
python -m pip install -r api/src/requirements.txt
```

After that, start the backend and frontend using the commands above.

### Windows Compatibility Note

The project requirements were updated so that `uvloop` is skipped on Windows, because `uvloop` does not support Windows.

This line is used in `api/src/requirements.txt`:

```
uvloop==0.22.1; platform_system != "Windows"
```

This allows Windows users to install dependencies successfully.

---

## Azure / Blob Storage Note

For local development, the current setup uses a local-output approach for processed images.

Azure deployment and Azure Blob Storage configuration has been added in 'main' branch, README.md.

### Project Structure

```
carclinch-bg-removal-api/
│
├── api/
│   └── src/
│       ├── main.py
│       ├── requirements.txt
│       └── ...
│
├── frontend/
│   ├── app.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── styles.css
│
└── README.md
```

### Current Development Notes

- Frontend is implemented in Flask
- Backend is implemented in FastAPI
- Single-model processing works locally
- Multi-model mode is currently disabled in the frontend
- Azure deployment instructions has been added in 'main' README.md
