# Contributing to CineAI

First off, thank you for considering contributing to CineAI! It's people like you that make open-source platforms such a great community.

## 🛠️ Local Development Setup

To get the complete stack running locally for development:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alive-xd/CineAI.git
   cd CineAI
   ```

2. **Configure Environment Variables:**
   - Copy `backend/.env.example` to `backend/.env`
   - Copy `frontend/.env.example` to `frontend/.env.local`
   - Ensure you insert your TMDb API Key inside `backend/.env`.

3. **Bootstrap the Infrastructure:**
   We provide a helper script to seamlessly spin up PostgreSQL, Redis, and Qdrant locally.
   ```bash
   ./scripts/bootstrap.sh
   ```

4. **Run the Backend (FastAPI):**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8001
   ```

5. **Run the Frontend (Next.js):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 📝 Pull Request Process

1. Fork the repository and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure your code passes all linting (`flake8` / `black` for Python, `eslint` for Next.js).
4. Update the `README.md` with details of changes to the interface or architecture, if applicable.
5. Create a descriptive Pull Request explaining *why* you made the change, not just *what* you changed.
