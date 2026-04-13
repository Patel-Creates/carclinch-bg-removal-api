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
