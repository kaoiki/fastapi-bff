# FastAPI BFF Template

A lightweight Backend-for-Frontend (BFF) built with FastAPI and Supabase, designed for rapid MVP development and future scalability.

---

## 🚀 Overview

This project serves as a reusable BFF template for building modern web applications.

Architecture:

Frontend (Vercel)
→ FastAPI BFF
→ Supabase (Database + Auth + Storage)

The BFF acts as a thin layer handling:

* Request validation
* Simple business logic
* External integrations (AI, APIs)
* Security controls

---

## 🧱 Tech Stack

* FastAPI (Python 3.11+)
* uv (dependency management)
* Uvicorn / Gunicorn
* Supabase (DB + Auth + Storage)
* Pydantic

---

## 📁 Project Structure

```
fastapi-bff/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── models/
│   └── utils/
├── pyproject.toml
├── uv.lock
├── .env
├── .gitignore
└── README.md
```

---

## ⚙️ Setup

### 1. Create environment

```bash
conda create -n fastapi-bff python=3.11 -y
conda activate fastapi-bff
```

### 2. Install uv

```bash
pip install uv
```

### 3. Install dependencies

```bash
uv sync
```

---

## ▶️ Run (Development)

```bash
uv run uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000/api/health
```

---

## 🚀 Run (Production)

```bash
uv run gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  -w 4
```

---

## 📦 API Response Format

All APIs follow a unified structure:

### Success

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### Error

```json
{
  "code": 1,
  "message": "error message",
  "data": null
}
```

---

## 🔑 Environment Variables

Create a `.env` file:

```
SUPABASE_URL=
SUPABASE_KEY=
```

---

## 📌 Design Principles

* Thin BFF layer (no heavy backend logic)
* Supabase as data backbone
* Clean API contracts (future Spring Boot migration)
* Minimal and fast MVP development

---

## 🧭 Roadmap

* Posts / Comments
* Dog Profiles
* AI Care (DeepSeek)
* Products & Reviews
* Knowledge Base

---

## 📄 License

MIT
