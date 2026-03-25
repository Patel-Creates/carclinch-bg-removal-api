
# Architecture Decision Record (ADR)

This document explains the key technical decisions we made during this project, why we made them, and what we considered before deciding.

## Decision 1 — Deployment Platform

**Decision:** Deploy on **Azure Container Apps** instead of Azure Durable Functions.

**Why:**
Our API receives an image, processes it, and returns a result in ~2 seconds. Durable Functions are built for long-running workflows (minutes to hours) — that's not what we're doing. Container Apps runs our existing FastAPI app directly with no extra complexity.

**What we considered:**

- Azure Durable Functions → adds unnecessary orchestration overhead (~4–8s extra latency)
- Render (current) → not Azure-native, can't serve multiple models

## Decision 2 — Background Removal Model


**Decision:** Use **ISNet-general-use** as the default model, with U2-Net and Silueta available as options.

**Why:**
We ran a formal model evaluation (see `model_eval/`) comparing multiple models on car images. ISNet produced the cleanest edges around complex vehicle shapes like mirrors and wheels. All models are stored in ONNX format. The `rembg` library uses ONNX Runtime to load and run whichever model is requested. Switching models requires no infrastructure change — just a different model name parameter. No PyTorch or TensorFlow is needed, keeping the Docker image lightweight.

**Available models:**

| Model | Quality | Speed | Format |
|---|---|---|---|
| `isnet-general-use` | Best | Medium | ONNX |
| `u2net` | Good | Medium | ONNX |


## Decision 3 — Image Storage

**Decision:** Use **Azure Blob Storage** for storing uploaded and processed images.

**Why:**
Azure Container Apps are stateless — files saved locally disappear when the container restarts. Blob Storage persists files across restarts and deployments. It also lets us return a direct download URL (SAS URL) to the frontend instead of streaming the file through the API.

**Storage containers:**

- `inputs/` — original uploaded images
- `outputs/` — processed result images
- `backgrounds/` — preset showroom background images

## Decision 4 — Infrastructure as Code

**Decision:** Use **Terraform** to provision all Azure resources.

**Why:**
The client requested a Terraform script. It also means any team member can recreate the entire Azure environment from scratch with one command (`terraform apply`), and all infrastructure changes are version-controlled in GitHub alongside the code.

---

## Decision 5 — CI/CD Pipeline

**Decision:** Use **GitHub Actions** to automatically build and deploy on every merge to `main`.

**Why:**
The team already uses GitHub. GitHub Actions integrates natively with Azure and is free for public repos. Every deployment is tied to a specific commit SHA so we can trace exactly what's running in production.

**Flow:**

```
Merge to main → GitHub Actions builds Docker image
             → Pushes to Azure Container Registry
             → Azure Container App pulls latest image
```

## Decision 6 — Model Session Caching

**Decision:** Cache the AI model session in memory using `lru_cache`.

**Why:**
Loading an ONNX model takes 3–5 seconds. Without caching, every single API request would reload the model — making the app unusably slow. With `lru_cache(maxsize=1)`, the model loads once and stays in memory. When the user switches models, the old one is removed and the new one loads once.
