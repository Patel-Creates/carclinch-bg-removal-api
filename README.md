# CarClinch — AI Background Removal & Replacement API

> Capstone Project | CST8922 Applied Projects | Algonquin College | Winter 2026

---

## Project Overview

CarClinch is an AI-powered background removal and replacement API built for an industry client in the automotive marketplace space. The system allows car dealership staff to upload vehicle photos and receive professionally processed images with the background removed and replaced with a clean showroom environment automatically, in seconds.

This project was developed as a proof of concept (POC) demonstrating the technical feasibility of integrating open-source AI vision models into a cloud-hosted API pipeline.

---

## Problem Statement

Car dealership listings require clean, professional images of vehicles against neutral or showroom backgrounds. Manually editing photos is time-consuming and expensive. CarClinch needed an automated solution that could:

- Remove complex backgrounds from car photos (including other vehicles, signage, and objects)
- Replace the background with a clean showroom environment
- Run reliably in the cloud with low latency
- Allow testing of multiple AI models to compare output quality

---

## Features

**Background Removal** uses the ISNet-general-use model via the `rembg` library to cleanly isolate vehicles from complex backgrounds including other cars, signage, and outdoor environments.

**Single-model Background Replacement** composites the extracted foreground car onto a new showroom background image using the default model, returning a stable backend image URL stored in Azure Blob Storage.

**Multi-model Background Replacement** processes the same car and background image pair across all supported models simultaneously, returning one result per model. Partial failure handling is built in & if one model fails, the remaining results are still returned.

**Private Image Serving** delivers processed images securely through backend Azure Blob Storage URLs rather than exposing them publicly, keeping client assets protected.

**Model Evaluation Suite** provides an offline benchmarking tool to measure and compare model quality using IoU, F1 and MAE metrics which was used to justify the selection of ISNet as the default model.

**Frontend Integration**  A frontend interface has been developed and is available on the `frontend-final` branch, ready to be integrated with this API.

---

## Tech Stack 🛠️

- **FastAPI**: Python web framework for the API layer
- **Python**: Core language
- **Docker**: Containerization
- **Azure Blob Storage**: Processed image storage and private serving
- **Azure Container Registry (ACR)**: Docker image registry
- **Azure Container Apps**: Serverless container hosting
- **Terraform**: Infrastructure as Code

---

## Architecture 🏗️

**CI/CD:** GitHub Actions → Azure Container Registry → Azure Container Apps

**Infrastructure:** All Azure resources provisioned via Terraform (ACR, Container App, Blob Storage, Log Analytics)

**Pipeline triggers:** Path-based pipeline which only runs on code changes, not README or docs updates

**Linting:** `ruff` with E402 suppressed for intentional `sys.path` manipulation imports

**Model caching:** YOLO and rembg download models at runtime into `/app/models` (`YOLO_CONFIG_DIR=/app/models`), which is set as a writable directory in the Dockerfile

### CI/CD Workflows

| Workflow | File | Trigger | Steps |
|---|---|---|---|
| CI | `.github/workflows/ci.yml` | Push / PR to `main` | Lint (`ruff`) + Docker build |
| CD | `.github/workflows/cd.yml` | Merge to `main` | Lint + build + push to ACR + deploy to Azure Container Apps |

For full architecture decisions and rationale, see [`docs/ADR.md`](docs/ADR.md)

---

## Repository Structure 📁

```
carclinch-bg-removal-api/
├── api/                    ← FastAPI application
│   ├── src/
│   │   ├── main.py         ← API endpoints
│   │   └── requirements.txt← API dependencies
│   ├── test/
│   │   └── test_main.py    ← pytest test suite
│   ├── Dockerfile          ← Container definition (includes /app/models writable dir)
│   └── ruff.toml           ← Linter config (E402 suppressed)
├── core/
│   └── processor.py        ← Shared AI processing library
├── model_eval/             ← Offline model evaluation suite
│   ├── dataset/
│   ├── dataset.py
│   ├── eval.py
│   ├── metrics.py
│   └── requirements.txt
├── docs/
│   └── ADR.md              ← Architecture Decision Record
├── infrastructure/         ← Terraform Infrastructure as Code
├── .github/
│   └── workflows/
│       ├── ci.yml          ← Lint + Docker build on PR
│       └── cd.yml          ← Build + push to ACR + deploy on merge
└── README.md               ← You are here
```

---

## Quick Start

### Prerequisites

- Python 3.13+
- Docker
- Azure CLI (for deployment)

### Environment Variables

Create a `.env` file in the project root before running locally:

```env
AZURE_STORAGE_ACCOUNT_NAME=your_storage_account_name
AZURE_STORAGE_KEY=your_storage_account_key
AZURE_STORAGE_CONTAINER_NAME=processed-images
IMAGE_BASE_DIR=images
```

### Run Locally

```bash
# Clone the repo
git clone https://github.com/Patel-Creates/carclinch-bg-removal-api.git
cd carclinch-bg-removal-api

# Create and activate a virtual environment
python3.13 -m venv .venv
source .venv/bin/activate        # Mac/Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r api/src/requirements.txt

# Run the API
uvicorn api.src.main:app --reload --port 8000
```

- API available at: `http://localhost:8000`
- Interactive docs at: `http://localhost:8000/docs`

> **Note:** Make sure your virtual environment is activated (you'll see `(.venv)` in your terminal) before installing dependencies or running the API.

### Run with Docker

```bash
# Build
docker build -t carclinch-api ./api

# Run
docker run -p 8000:8000 --env-file .env carclinch-api
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check / basic test endpoint |
| POST | `/replace-background` | Process one car image with one background using the default model — returns a stable backend image URL |
| POST | `/replace-background-all-models` | Process the same car + background pair with all supported models & returns one result per model |
| GET | `/images/{blob_name}` | Serve a processed image privately from Azure Blob Storage |

### Multi-model Request (`/replace-background-all-models`)

Multipart form data:

| Field | Type | Description |
|---|---|---|
| `image` | file | Foreground car image |
| `background` | file | Replacement background image |
| `car_size` | number (1–100) | Car size as percentage of frame |
| `smart_placement` | boolean | Enable smart car placement |

### Multi-model Response Format

```json
{
  "input_foreground": "fg_car.jpg",
  "input_background": "bg_showroom.jpg",
  "total_models": 8,
  "successful_models": 7,
  "failed_models": 1,
  "car_size_percentage": "60.0%",
  "smart_placement_enabled": true,
  "results": [
    {
      "model": "u2net",
      "status": "success",
      "output_filename": "multi_u2net_fg_car_replaced.png",
      "output_path": "images/output/multi_u2net_fg_car_replaced.png",
      "output_url": "/output/multi_u2net_fg_car_replaced.png"
    },
    {
      "model": "sam",
      "status": "failed",
      "error": "Processing failed for this model"
    }
  ],
  "message": "Multi-model background replacement completed"
}
```

> **Note:** Partial failure handling is built in & one model failing does not fail the whole request.

---

## Deployment to Azure ☁️

This project can also be deployed on Azure Container Apps using Terraform for infrastructure provisioning.

```bash
# Provision infrastructure
cd infrastructure/
terraform init
terraform plan
terraform apply
```

CI/CD is handled by GitHub Actions & every merge to `main` automatically builds and pushes the Docker image to Azure Container Registry and deploys to Azure Container Apps.

---

## Model Evaluation 📊

The `model_eval/` suite was used to benchmark multiple background removal models on car image datasets to justify our model selection.

| Model | IoU | Notes |
|---|---|---|
| `isnet-general-use` | Best | Selected as default & strongest edge quality on vehicles |
| `u2net` | Good | Original model, solid general performance |
| `silueta` | Fair | Fastest but lower accuracy |

---

## Team 👥 

| Name | Role |
|---|---|
| Islam Gomaa | Professor |
| Mr Ahmed | Industry Client |
| Dharti Patel | Group leader |
| Muhire Josue | Developer |
| Olga Durham | Developer |
| Kylath George | Developer |
| Kelvin Ngabo | Developer |

---

## 📅 Project Timeline

| Sprint | Focus | Status |
|---|---|---|
| Sprint 1 | Background removal API, model evaluation | ✅ Complete |
| Sprint 2 | Background replacement, architecture design | ✅ Complete |
| Sprint 3 | Azure deployment, Terraform, CI/CD, documentation | ✅ complete |