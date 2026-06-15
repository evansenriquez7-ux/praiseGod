# CCMed Firebase & Google Cloud Run Setup Guide

This document explains the architecture and deployment process for the CCMed Adaptive Mastery Engine. 

We migrated the application from a local Mac Mini server to a fully serverless, highly-available stack on Google Cloud (Blaze Plan). This guide explains how to properly deploy and maintain it.

## 🏗 Architecture Overview

1. **Backend (FastAPI)**: Hosted natively as a **Google Cloud Run** container in the `asia-southeast1` (Singapore) region. 
   * *Why Cloud Run instead of Firebase Functions?* Firebase Functions uses a single-threaded Python WSGI wrapper which deadlocks when trying to run the asynchronous `a2wsgi` adapter for FastAPI. Deploying FastAPI natively to Cloud Run using `uvicorn` completely bypasses this deadlock.
2. **Database (Neon Postgres)**: A serverless Postgres database hosted in Singapore (AWS `ap-southeast-1`) for low-latency connections to the backend.
3. **Frontend (Vite / React)**: Hosted on **Firebase Hosting**.
4. **API Routing**: Firebase Hosting's `firebase.json` automatically proxies any request hitting `/api/**` to the native Cloud Run service.

---

## 🚀 Deployment Playbook

### 1. Deploy the Backend (Cloud Run)
Do not use `firebase deploy --only functions`. Instead, we deploy the backend natively using the `gcloud` CLI so that our `Dockerfile` is respected and FastAPI runs flawlessly under Uvicorn.

Run this command from the project root. Make sure to pass your live Neon Database URL securely via the `--set-env-vars` flag:

```bash
gcloud run deploy ccmed-api \
  --source . \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --project praisegod-edu \
  --set-env-vars="DATABASE_URL=postgresql://neondb_owner:<YOUR_PASSWORD>@ep-winter-bird-ao6aql6n.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
```

*Note: The `Dockerfile` has been explicitly configured to use `python:3.12-slim` and executes `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.*

### 2. Configure Firebase Routing
Ensure your `firebase.json` contains the following rewrite rule under the `hosting` section. This connects your Firebase custom domains directly to the Cloud Run backend without any CORS preflight blocking:

```json
"rewrites": [
  {
    "source": "/api/**",
    "run": {
      "serviceId": "ccmed-api",
      "region": "asia-southeast1"
    }
  },
  {
    "source": "**",
    "destination": "/index.html"
  }
]
```

### 3. Build & Deploy the Frontend (Firebase Hosting)
Whenever you make changes to the React frontend in the `/frontend` directory, you must rebuild the static bundle and push it to Firebase Hosting.

```bash
cd frontend
npm run build
cd ..
firebase deploy --only hosting
```

---

## 💻 Local Development

When developing locally, **do not use the `functions-framework`** to test the backend, as it will simulate the deadlocking single-threaded environment.

Instead, run the stack natively using your existing management script:

```bash
./manage.sh start
```

This starts the native `uvicorn` ASGI server on port `8000` and the Vite frontend on port `5173`. 

---

## 🛡 Common Pitfalls & Solutions

* **Cold Start Timeouts**: Neon Serverless Database and Cloud Run both scale down to zero when idle to save money. The first request after a long idle period may take 10–20 seconds to wake up the database. The frontend `App.jsx` connection check timeout is explicitly set to `30000ms` (30 seconds) to patiently wait for this cold start.
* **CORS Errors**: If you register a new domain for your Firebase app, you MUST explicitly add it to the `allow_origin_regex` list in `backend/app/main.py`. If it is not whitelisted, FastAPI will silently block the preflight `OPTIONS` request, resulting in a frontend `Connection Timeout`.
* **Missing Profiles / Database Connection**: The Cloud Run backend explicitly connects to the Neon DB using the `DATABASE_URL` injected during deployment. If you ever need to pull data from your old Mac Mini local Postgres DB (`ccmed`), use `pg_dump` and import it into Neon via `psql`.
