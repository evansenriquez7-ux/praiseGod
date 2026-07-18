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

## 2. Automated CI/CD (GitHub Actions Workflows)

The application leverages GitHub Actions for automated testing and deployment.

### A. Validation Gate (`.github/workflows/validate-pgen.yml`)
*   **Triggers:** Every PR and push targeting `backend/**` or `data/**`.
*   **Pipeline:** Installs dependencies and runs the validation harness:
    ```bash
    python -m backend.app.practice_gen.validation.run_all
    ```
*   **No Fallbacks:** Unlike the hosting workflow, this pipeline has **no `|| true` fallbacks or `continue-on-error` options**. If a single validation fails, the job must fail, blocking deployments.

### B. Frontend Flow (`.github/workflows/firebase-hosting-merge.yml`)
*   **Triggers:** Pushes targeting the `main` branch.
*   **Pipeline:** Installs dependencies and builds the bundle (`cd frontend && npm install && npm run build`), then pushes to Firebase Hosting.

### C. Backend Flow (`.github/workflows/deploy-backend.yml`)
*   **Triggers:** Pushes containing modifications inside `backend/` or to the root `Dockerfile`.
*   **Pipeline:** Builds a fresh Docker container image using the `Dockerfile` configuration and updates Google Cloud Run. **Requires the Validation Gate to pass successfully.**

---

## 3. Required Secrets & Configuration Keys

Because the backend dynamically routes all database queries based on the `DATABASE_URL` environment variable, configure it properly across environments.

### A. Production CI/CD (GitHub Actions)
Configure the following under **GitHub Settings > Secrets and variables > Actions**:
*   `FIREBASE_SERVICE_ACCOUNT_PRAISEGOD_EDU`: Service account JSON credential.
*   `PROJECT_ID`: Set to `praisegod-edu`.
*   `DATABASE_URL`: Live Neon production database connection string.

### B. GitHub Codespaces Environment
*   Configure `DATABASE_URL` under **GitHub Settings > Secrets and variables > Codespaces**.

### C. Local Development (Mac/Windows)
*   Create a `.env` file in the root of the project with `DATABASE_URL="..."`.

---

## 4. Operational Playbook & Maintenance

### Manual Backend Deployment (Fallback)
```bash
gcloud run deploy ccmed-api \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --project praisegod-edu \
  --set-env-vars="DATABASE_URL=..."
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
Cloud Run and Neon scale to zero on idle. Initial wake-up connections can consume up to 10–20 seconds. The frontend timeout is set to `30000ms`.

### CORS Mismatches
Whitelist new subdomains/custom domains in `allow_origin_regex` in `backend/app/main.py`.

### Firebase Hosting "Current Active Version" (400 Error)
When pushing commits that don't change the frontend code, the deploy step in `firebase-hosting-merge.yml` may fail with a `400` error because Vite generates an identical bundle hash.
*   **Solution:** The deployment command has an appended `|| true`. This is acceptable because a redundant deployment contains no code changes, so keeping the pipeline green is safe. **Do not copy this `|| true` pattern into validation gates**, where actual code verification is running.

---

## 6. Practice Problem Generation Rules

The pg pipeline contract (and the machine-enforced test validations) now live in [`pgen_contract.md`](./pgen_contract.md). See that document for all binding generation constraints.

---

## 7. Remote Development Environment (VS Code SSH)

Access the host machine locally via **VS Code Remote-SSH**.

### Configuring Full Disk Access (FDA)
1. **Disabled Tailscale's Custom SSH Interceptor:** Run `tailscale up --ssh=false`.
2. **Fallback to Native macOS `sshd`:** Routes directly to the standard macOS `sshd`.
3. **Inherited FDA:** Grant full disk access to `/usr/sbin/sshd` in System Settings.