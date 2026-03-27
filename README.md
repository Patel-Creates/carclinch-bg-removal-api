# CarClinch — AI Background Removal & Replacement API

> Capstone Project | CST8922 Applied Projects | Algonquin College | Winter 2026

## Project Overview

CarClinch is an AI-powered background removal and replacement API built for an industry client in the automotive marketplace space. The system allows car dealership staff to upload vehicle photos and receive professionally processed images with the background removed and replaced with a clean showroom environment — automatically, in seconds.

This project was developed as a proof of concept (POC) demonstrating the technical feasibility of integrating open-source AI vision models into a cloud-hosted API pipeline.

## Problem Statement

Car dealership listings require clean, professional images of vehicles against neutral or showroom backgrounds. Manually editing photos is time-consuming and expensive. CarClinch needed an automated solution that could:

- Remove complex backgrounds from car photos (including other vehicles, signage, and objects)
- Replace the background with a clean showroom environment
- Run reliably in the cloud with low latency
- Allow testing of multiple AI models to compare output quality

## Features

- **Background Removal** — AI-powered background removal using ISNet-general-use via the `rembg` library
- **Background Replacement** — Composite the foreground car onto a new showroom background
- **Model Evaluation Suite** — Offline benchmarking suite to measure and compare model quality (IoU, F1, MAE)
- **Cloud Deployment** — Fully containerized and deployed on Azure Container Apps with Terraform-managed infrastructure

## S Architecture

**CI/CD:** GitHub Actions → Azure Container Registry → Azure Container Apps

**Infrastructure:** All Azure resources provisioned via Terraform (working on this currently)

> For full architecture decisions and rationale, see ( will link the ADR once it is merged )

## 📁 Repository Structure

```
carclinch-bg-removal-api/
├── api/                    ← FastAPI application
│   ├── src/
│   │   └── main.py         ← API endpoints
│   └── requirements.txt    ← API dependencies
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
├── terraform/              ← Infrastructure as Code (coming soon)
├── .github/
│   └── workflows/          ← GitHub Actions CI/CD (coming soon)
├── Dockerfile
└── README.md               ← You are here
```

##  Documentation

| Component | README |
|---|---|
|  Backend API (FastAPI) | [api/README.md](api/README.md) |
|  Model & Core Processor | [core/README.md](core/README.md) |
|  Model Evaluation Suite | [model_eval/README.md](model_eval/README.md) |
|  Architecture Decisions | [docs/ADR.md](docs/ADR.md) |
|  Frontend |  (will add once merged) |

## Quick Start

### Prerequisites

- Python 3.13+
- Docker
- Azure CLI (for deployment)

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
pip install -r api/requirements.txt

# Run the API
uvicorn api.src.main:app --reload --port 8000
```

API will be available at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

> **Note:** Make sure your virtual environment is activated (you'll see `(.venv)` in your terminal) before installing dependencies or running the API.

### Run with Docker

```bash
# Build
docker build -t carclinch-api .

# Run
docker run -p 8000:8000 carclinch-api
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/upload-image` | Remove background from uploaded image |
| `POST` | `/replace-background` | Remove + replace background with new image |

> Full endpoint documentation: (will be josue's new merge- Link here please)

## Deployment

This project is deployed on **Azure Container Apps** using **Terraform** for infrastructure provisioning.

```bash
# Provision infrastructure
cd terraform/
terraform init
terraform plan
terraform apply
```

CI/CD is handled by GitHub Actions — every merge to `main` automatically builds and deploys the latest Docker image.

> Full deployment steps: (will be josue's new merge- Link here please)

##  Model Evaluation

The `model_eval/` suite was used to benchmark multiple background removal models on car image datasets to justify our model selection.

| Model | IoU | Notes |
|---|---|---|
| `isnet-general-use` | Best | Selected as default — strongest edge quality on vehicles |
| `u2net` | Good | Original model, solid general performance |
| `silueta` | Fair | Fastest but lower accuracy |

> Full evaluation methodology: [model_eval/README.md](model_eval/README.md)

## Team

| Name | Role |
|---|---|



**Professor:** Islam Gomaa
**Client:** CarClinch

## Project Timeline

| Sprint | Focus | Status |
|---|---|---|
| Sprint 1 | Background removal API, model evaluation | Complete |
| Sprint 2 | Background replacement, architecture design | Complete |
| Sprint 3 | Azure deployment, Terraform, CI/CD, documentation | 🔄 In Progress |

---

## Scope Note
