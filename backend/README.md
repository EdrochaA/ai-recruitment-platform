# AI Recruitment Platform

Backend service for an AI-powered recruitment platform focused on intelligent CV filtering and candidate selection.

---

## 📌 Project Overview

This project is part of a final degree project (TFG) in Computer Engineering.  
The goal is to build a scalable system that allows companies to manage job offers and efficiently filter candidates using artificial intelligence techniques.

In this first phase, the backend foundation has been implemented, including a clean architecture design and the initial job offer management module.

---

## 🏗️ Architecture

The project follows a **clean (hexagonal) architecture**, separating responsibilities into different layers:

- **Domain** → Core business entities and interfaces  
- **Application** → Use cases containing business logic  
- **Infrastructure** → Frameworks, API routes and persistence  
- **Shared** → Common dependencies and configuration  

---

## ⚙️ Tech Stack

- Python 3.10+
- FastAPI
- Uvicorn
- Pydantic
- uv (modern dependency manager)

---

## 📁 Project Structure

backend/
├── app/
│   ├── main.py
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── shared/
├── pyproject.toml
├── uv.lock
└── README.md

---

## 🚀 Features (Phase 1)

- Create job offers  
- List job offers  

---

## 🔌 API Endpoints

POST /job-offers  
GET /job-offers  

---

## 🧠 Domain Model

**JobOffer**
- id
- title
- description
- location
- status
- created_at

---

## 🔄 Persistence

In-memory repository:
InMemoryJobOfferRepository

---

## ▶️ Running the Project

uv sync  
uv run python -m uvicorn app.main:app --reload  

Docs:
http://127.0.0.1:8000/docs

---

## 🎯 Phase Goal

- Backend foundation  
- Scalable architecture  
- First functional module  

---

## 🚧 Next Steps

- Applications module  
- CV upload  
- AWS integration  
- AI filtering  

---

## 📚 References

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Pydantic Documentation: https://docs.pydantic.dev/
- Uvicorn Documentation: https://www.uvicorn.org/
- Clean Architecture (Robert C. Martin): https://8thlight.com/blog/uncle-bob/2012/08/13/the-clean-architecture.html
- Hexagonal Architecture (Alistair Cockburn): https://alistair.cockburn.us/hexagonal-architecture/
- AWS Architecture Best Practices: https://docs.aws.amazon.com/architecture/
