# CCMed Serverless Infrastructure & Deployment Playbook

This document details the serverless architecture, configuration setup, and automated CI/CD integrated workflows for the CCMed Adaptive Mastery Engine.

---

## 1. Architecture Overview

The system is hosted on a highly-available, fully serverless stack on Google Cloud (Blaze Plan) and Neon DB:

1.  **Backend (FastAPI):** Hosted natively as a **Google Cloud Run** container in the `asia-southeast1` (Singapore) region.
    *   *Note on Deadlocks:* We explicitly bypass the single-threaded WSGI limits of traditional Firebase Functions by using Cloud Run + `uvicorn` to handle asynchronous ASGI requests.
2.  **Database (Neon Postgres):** Serverless Postgres database hosted in Singapore (AWS `ap-southeast-1`) for low-latency queries.
3.  **Frontend (Vite / React):** Hosted on **Firebase Hosting**.
4.  **API Routing & Proxying:** Firebase Hosting (`firebase.json`) automatically routes `/api/**` traffic directly to the Google Cloud Run service, avoiding CORS preflight blockages.

---

## 2. Automated CI/CD (GitHub Actions Workflow)

The application leverages GitHub Actions for modern automated deployment upon pushing code to the `main` branch.

### Frontend Flow (`.github/workflows/firebase-hosting-merge.yml`)
*   **Triggers:** Pushes targeting the `main` branch.
*   **Pipeline:** Installs dependencies and builds the bundle (`cd frontend && npm install && npm run build`), then automatically pushes the static directory to Firebase Hosting.

### Backend Flow (`.github/workflows/deploy-backend.yml`)
*   **Triggers:** Pushes containing modifications inside `backend/` or to the root `Dockerfile`.
*   **Pipeline:** Builds a fresh Docker container image using the explicit `Dockerfile` configuration and updates the Google Cloud Run server instances.

---

## 3. Required Secrets & Configuration Keys

To enable automated pipelines, configure the following under **GitHub Settings > Secrets and variables > Actions**:

*   `FIREBASE_SERVICE_ACCOUNT_PRAISEGOD_EDU`: Service account JSON credential possessing authorization roles for: *Cloud Run Admin*, *Firebase Hosting Admin*, *Service Account User*, and *Artifact Registry Writer*.
*   `PROJECT_ID`: Set to `praisegod-edu`.
*   `DATABASE_URL`: Connection string containing full secure parameters pointing to the live Neon production instance.

---

## 4. Operational Playbook & Maintenance

### Manual Backend Deployment (Fallback)
If manual deployment or updating environment strings is ever required, run the command below from the workspace root:

```bash
gcloud run deploy ccmed-api \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --project praisegod-edu \
  --set-env-vars="DATABASE_URL=postgresql://neondb_owner:<YOUR_PASSWORD>@ep-winter-bird-ao6aql6n.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
```

### Manual Frontend Deployment (Fallback)
```bash
cd frontend
npm run build
cd ..
firebase deploy --only hosting
```

---

## 5. Common Pitfalls & Solutions

### Cold Start Timeouts
Because both Cloud Run and Neon Serverless Database scale down to zero during idle periods to eliminate resource costs, initial wake-up connections can consume up to 10–20 seconds. The frontend client connection check timeout is explicitly set to `30000ms` (30 seconds) to wait out database wakes cleanly.

### CORS Mismatches
If registering or adding a new subdomain or custom domain for your Firebase deployment, you **MUST** whitelist it in the `allow_origin_regex` inside `backend/app/main.py`. Unlisted origins will result in silent preflight `OPTIONS` blocks.

### Data Dependency Copies
When adding new data configurations or knowledge graph models, verify that the `Dockerfile` specifies the target subdirectory (e.g., `data/`) so it correctly copies files inside the runtime container context.
