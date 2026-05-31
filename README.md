<div align="center">

<img src="Assets/cineai-logo.png" alt="CineAI Logo" width="80" height="80" />

# CineAI

### AI-Powered Movie Recommendation Platform

*Discover movies through meaning, emotion, and personal taste — not just keywords*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://postgresql.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-dc244c?style=flat-square)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)](#license)

<br/>

> **"Mind-bending sci-fi"** · **"Movies like Interstellar but sadder"** · **"Dark psychological thrillers"**
>
> CineAI understands what you mean — not just what you type.

<br/>

![Home Dashboard](Assets/home-dashboard.png)

</div>

---

## What is CineAI?

CineAI is a production-grade, full-stack AI movie recommendation platform built from scratch. It combines **semantic vector search**, **hybrid recommendation algorithms**, **collaborative filtering**, and **explainable AI** to deliver highly personalised movie discovery experiences.

Unlike traditional movie platforms that rely on keyword matching or simple genre filters, CineAI understands natural language queries, learns user taste over time, and explains every recommendation it makes.

```
User types:  "something emotional and mind-bending like Interstellar"
CineAI:      Encodes query → searches 384-dim vector space → retrieves semantically
             similar movies → ranks using hybrid engine → returns with explanations
```

---

## Key Achievements

- Built a hybrid recommendation engine combining semantic, content-based, collaborative, and popularity-based recommendation signals
- Implemented vector-based semantic search using SentenceTransformers and Qdrant
- Designed adaptive user taste learning powered by ratings, watchlists, and interaction history
- Developed explainable recommendations through score attribution and recommendation reasoning
- Integrated PostgreSQL, Redis, and Qdrant into a production-oriented AI architecture
- Containerized the complete platform using Docker Compose
- Designed a scalable FastAPI service architecture with clear separation of business logic, machine learning components, and API layers

---

## Screenshots

<table>
<tr>
<td width="50%">

**Home & Recommendations**
![Home Dashboard](Assets/home-dashboard.png)
*Personalised AI recommendations with match scores and reasoning*

</td>
<td width="50%">

**Semantic Search**
![Semantic Search](Assets/semantic-search.png)
*Natural language movie discovery powered by vector embeddings*

</td>
</tr>
<tr>
<td width="50%">

**Movie Details**
![Movie Details](Assets/movie-details.png)
*Rich movie information with AI insights and similar movies*

</td>
<td width="50%">

**Taste Analytics**
![Taste Analytics](Assets/taste-analytics.png)
*AI-computed taste fingerprint with genre radar and engine weights*

</td>
</tr>
</table>

---

## System Architecture

![CineAI System Architecture](Assets/blob/8cfbd8b241591978672d4a69b47061a4ccdf47d4/Assets/ChatGPT%20Image%20May%2031%2C%202026%2C%2010_04_44%20PM.png)

The platform is built on a clean layered architecture separating the frontend presentation layer, FastAPI backend, ML/AI pipeline, and data infrastructure — each independently scalable and maintainable.

---

## AI Recommendation Pipeline

![AI Recommendation Pipeline](Assets/ChatGPT_Image_May_30__2026__10_56_15_PM.png)

Every recommendation passes through a 9-stage pipeline — from raw user input through embedding generation, vector retrieval, hybrid scoring, diversity re-ranking, to final personalised output — with a continuous learning loop that improves over time.

### Hybrid Ranking Formula

```
Final Score = (0.35 × Semantic) + (0.30 × Content) + (0.25 × Collaborative) + (0.10 × Popularity)
```

| Signal | Weight | Description |
|--------|--------|-------------|
| **Semantic** | 35% | Cosine similarity in 384-dim embedding space via Qdrant ANN |
| **Content** | 30% | TF-IDF similarity across genre, director, cast, keywords |
| **Collaborative** | 25% | SVD matrix factorisation on user-item rating matrix |
| **Popularity** | 10% | Vote-weighted recency-decayed popularity score |

> Weights are **adaptive per user** — they shift automatically based on your feedback (likes, dismissals, ratings) using an Exponential Moving Average update rule.

---

## Core Features

### 🔍 AI Semantic Search
Search using natural language instead of exact keywords. The query is encoded into a 384-dimensional vector and matched against the movie embedding space in Qdrant.

```
"movies about loneliness"          → Her, Lost in Translation, Aftersun
"mind-bending thriller"            → Inception, Memento, Shutter Island
"something like Interstellar"      → Arrival, Contact, 2001: A Space Odyssey
"emotional sci-fi about grief"     → Annihilation, Arrival, Melancholia
```

### 🤖 Hybrid Recommendation Engine
Four recommendation signals fused with learned per-user weights. Not a single algorithm — a weighted ensemble that adapts to each user.

### 💡 Explainable AI
Every recommendation includes human-readable reasoning:
```
✦ Matches your love of philosophical Sci-Fi
✦ Directed by Denis Villeneuve — a director you rate highly
✦ Similar emotional tone to movies you've rated 4.5+
```

### 🧠 User Taste Learning
A continuous taste profile updates after every interaction:
- Genre affinity weights per genre
- Director affinity scores
- Mood tag preferences
- Embedding centroid (weighted average of rated movie vectors)
- Per-user hybrid engine weights

### ❄️ Cold-Start Handling
New users receive trending + popular fallbacks until 5+ ratings are collected, at which point the full ML pipeline activates.

---

## Platform Metrics

| Metric | Value |
|--------|-------|
| Movies indexed | 2,992 |
| Semantic vectors in Qdrant | 1,439 |
| Embedding dimensions | 384 (all-MiniLM-L6-v2) |
| Recommendation cache TTL | 1 hour (Redis) |
| API endpoints | 18 |
| Database tables | 10 |
| Hybrid signals | 4 |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS | App Router, SSR, UI |
| **State** | Zustand, SWR | Auth state, data fetching |
| **Backend** | FastAPI, Python 3.11 | Async API, ML orchestration |
| **Database** | PostgreSQL 16 (Supabase) | Primary data store |
| **Vector DB** | Qdrant | Semantic search, ANN retrieval |
| **Cache** | Redis (Upstash) | Recommendation cache, rate limiting |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | 384-dim movie vectors |
| **Collaborative** | scikit-surprise (SVD) | Matrix factorisation |
| **Content** | scikit-learn (TF-IDF) | Metadata similarity |
| **Movie Data** | TMDb API | Movie metadata, posters |
| **Infra** | Docker Compose | Local orchestration |
| **Auth** | JWT + httpOnly refresh tokens | Secure authentication |

---

## Technical Challenges Solved

### Semantic Retrieval Without GPU
Running `all-MiniLM-L6-v2` fully on CPU with batch encoding and async Qdrant upserts — no GPU required, deployable on free-tier instances (512MB RAM).

### Hybrid Fusion with Explainability
Each of the 4 recommendation signals returns a normalised 0–1 score. The hybrid ranker fuses them with per-user learned weights, and the explainability layer attributes the dominant signal to generate human-readable reasons — not post-hoc rationalisation, but direct score attribution.

### Adaptive Per-User Weights
Instead of global recommendation weights, each user's hybrid formula adapts using Exponential Moving Average updates triggered by feedback actions. A user who consistently dismisses popularity-driven recommendations will see that weight decrease automatically.

### Cold-Start Problem
Three-tier fallback: trending movies → genre-affinity fallback → full ML pipeline (activates at 5+ ratings). No user ever sees an empty recommendation page.

### Vector Database on Free Tier
Qdrant's `indexing_threshold` is set to 20,000 vectors. Below this, vectors are stored and searchable in O(n) mode without ANN indexing — functional at current dataset scale, automatically upgrades to HNSW index as data grows.

### TMDb Access from Restricted Networks
External HTTPS connectivity issues solved via Cloudflare Worker proxy — zero additional cost, routes all TMDb API calls through a globally distributed edge network.

---

## Project Structure

```text
CineAI/
│
├── backend/
│   ├── app/
│   │   ├── api/            # 18 REST endpoints (auth, movies, search, recs)
│   │   ├── services/       # Business logic (movie, recommendation, auth)
│   │   ├── models/         # SQLAlchemy ORM — 10 database tables
│   │   ├── schemas/        # Pydantic v2 request/response schemas
│   │   ├── ml/
│   │   │   ├── embeddings/ # Encoder, pipeline, user profile centroid
│   │   │   ├── recommenders/ # Semantic, content, collaborative, hybrid
│   │   │   ├── explainability/ # Score attribution → human reasons
│   │   │   └── feedback/   # Adaptive weight updater (EMA)
│   │   └── core/           # Database, Redis, security, exceptions
│   │
│   ├── alembic/            # Database migrations
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── app/            # Next.js App Router — 8 pages
│       ├── components/     # 12 reusable UI components
│       ├── hooks/          # SWR data hooks
│       ├── lib/            # Typed API client, utilities
│       └── store/          # Zustand auth store
│
├── scripts/
│   ├── seed_movies.py      # Bulk TMDb ingest + embedding pipeline
│   └── bootstrap.sh        # One-command local setup
│
├── assets/                 # README screenshots & diagrams
└── docker-compose.yml      # Full stack orchestration
```

---

## Future Roadmap

- [ ] User-to-user collaborative filtering
- [ ] Conversational movie discovery (multi-turn)
- [ ] Emotion and tone metadata enrichment
- [ ] Upgrade embeddings to `bge-large-en` for better semantic quality
- [ ] A/B testing framework for recommendation strategies
- [ ] Social features — shared watchlists, friend recommendations
- [ ] Mobile app (React Native)
- [ ] Real-time recommendation updates via WebSocket

---

## About the Creator

<img src="https://avatars.githubusercontent.com/sushen-kumar" alt="Sushen Kumar" width="80" style="border-radius: 50%;" />

**Sushen Kumar** — Full-Stack Developer · AI/ML Engineer · Cybersecurity Researcher

I build intelligent software systems focused on AI, recommendation engines, cybersecurity tooling, and scalable backend architectures.

CineAI showcases modern recommendation system design using semantic retrieval, vector databases, hybrid ranking, explainable AI, and adaptive user preference learning.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Sushen_Kumar-0077B5?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/sushen-kumar/)
[![Email](https://img.shields.io/badge/Email-sushen.d3v%40gmail.com-EA4335?style=flat-square&logo=gmail)](mailto:sushen.d3v@gmail.com)
[![Instagram](https://img.shields.io/badge/Instagram-@sushen.pvt-E4405F?style=flat-square&logo=instagram)](https://instagram.com/sushen.pvt)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_a_Coffee-alivexd-FFDD00?style=flat-square&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/alivexd)

---

## Commercial Licensing

> Commercial licensing for CineAI is available upon request.

The commercial package includes:

- Complete FastAPI Backend
- AI Recommendation Engine
- Semantic Search Pipeline
- Hybrid Recommendation System
- Qdrant Integration
- PostgreSQL Database Models
- Redis Caching Layer
- Next.js Frontend
- Docker Configuration
- Database Migrations
- Seed & Utility Scripts
- Architecture Documentation

For licensing enquiries, partnerships, or commercial usage:

📧 sushen.d3v@gmail.com

💼 LinkedIn: https://www.linkedin.com/in/sushen-kumar/

> Includes complete source code, setup documentation, and architecture walkthrough.

---

## License

CineAI is proprietary software.

The source code, recommendation algorithms, machine learning pipeline, architecture, and supporting assets are protected and may not be reproduced, distributed, modified, or used commercially without explicit written permission.

© 2026 Sushen Kumar. All rights reserved.

---

<div align="center">

*Built with FastAPI · Next.js · PostgreSQL · Redis · Qdrant · sentence-transformers*

</div>
