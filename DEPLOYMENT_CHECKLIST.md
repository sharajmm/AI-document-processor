# 🚀 Streamlit Cloud Deployment Checklist

## 1. Codebase Preparation

- [x] Remove unused files and code
- [x] Ensure all dependencies are listed in `requirements.txt`
- [x] Add `packages.txt` for system dependencies (Tesseract, Tamil)
- [x] Add `.env` to `.gitignore` (never push secrets)

## 2. GitHub Setup

- [x] Push all code to a clean GitHub repository
- [x] Verify repo contains:
  - `app.py`, `requirements.txt`, `packages.txt`, all modules
  - No `.env` or secret files

## 3. Streamlit Cloud Setup

- [x] Connect GitHub repo to Streamlit Cloud
- [x] Add all environment variables (API keys, DB URL, etc.) in Streamlit Secrets
- [x] Streamlit will auto-install Python packages from `requirements.txt`
- [x] Streamlit will auto-install system packages from `packages.txt`

## 4. Post-Deployment Testing

- [x] Test document upload, OCR (English & Tamil), AI, export, tag search, audit log
- [x] Check UI and all features
- [x] Monitor logs for errors

## 5. Security

- [x] Keep secrets only in Streamlit Secrets
- [x] Rotate API keys regularly
- [x] Use private repo if needed

---

**Ready to deploy!**
