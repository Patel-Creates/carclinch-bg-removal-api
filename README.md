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
