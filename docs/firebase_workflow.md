# CCMed Project Workflow: GitHub & Firebase Integration

## Overview
This document outlines the standard operational workflow for maintaining the CCMed application, specifically focusing on the integration between the local development environment, GitHub repository, and Firebase deployment.

## Repository Structure & Automation
- **Frontend**: Located in `frontend/`. All builds must occur within this directory.
- **Backend**: Located in `backend/`.
- **Deployment**: Automated via GitHub Actions.

## Automated CI/CD
We use GitHub Actions to ensure seamless deployment.
- **Frontend**: `.github/workflows/firebase-hosting-merge.yml` triggers on push to `main`. It runs `cd frontend && npm install && npm run build` and deploys to Firebase Hosting.
- **Backend**: `.github/workflows/deploy-backend.yml` triggers on push to `main` (if changes are in `backend/` or `Dockerfile`). It builds a container image and deploys to Google Cloud Run.

## Required Secrets (GitHub Settings > Secrets and variables > Actions)
To enable automated deployments, the following secrets must be configured in the repository:
- `FIREBASE_SERVICE_ACCOUNT_PRAISEGOD_EDU`: Service Account JSON credentials with roles: Cloud Run Admin, Firebase Hosting Admin, Service Account User, Artifact Registry Writer.
- `PROJECT_ID`: Set to `praisegod-edu`.
- `DATABASE_URL`: The connection string for the production Neon database.

## Essential Maintenance Workflow
1. **Making Changes**: Apply surgical changes using `replace` or `write_file`.
2. **Commit & Push**: 
   ```bash
   git add .
   git commit -m "feat/fix: description"
   git push origin main
   ```
3. **Monitor Deployment**: Check the **Actions** tab in the GitHub repository to verify that both frontend and backend workflows complete successfully (green checkmark).

## Handling Configuration Issues
- **CORS**: If new domains are added, update `backend/app/main.py`'s `CORSMiddleware` `allow_origin_regex` to include the new domain.
- **Data Dependencies**: Ensure the `Dockerfile` correctly copies all necessary data directories (`data/`) for backend runtime availability.
