<div align="center">



# CineAI 

### AI-Powered Movie Recommendation Platform

*Discover movies through meaning, emotion, and personal taste — not just keywords*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?style=flat-square&logo=next.js)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql)](https://postgresql.org)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-dc244c?style=flat-square)](https://qdrant.tech)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)

<br/>

> **"Mind-bending sci-fi"** · **"Movies like Interstellar but sadder"** · **"Dark psychological thrillers"**
>
> CineAI understands what you mean — not just what you type.

<br/>

![Home Dashboard](Assets/home-dashboard.png)

</div>

---

## What is CineAI?

CineAI is a production-grade, full-stack AI movie recommendation platform built from scratch. It combines semantic vector search, hybrid recommendation algorithms, collaborative filtering, and explainable AI to deliver highly personalised movie discovery experiences.

Unlike traditional movie platforms that rely on keyword matching or simple genre filters, CineAI understands natural language queries, learns user taste over time, and explains every recommendation it makes.

```text
User types:  "something emotional and mind-bending like Interstellar"
CineAI:      Encodes query → searches 384-dim vector space → retrieves semantically
             similar movies → ranks using hybrid engine → returns with explanations
```

---

## Key Achievements

- **Hybrid Recommendation Engine:** Combined semantic, content-based, collaborative, and popularity-based recommendation signals into a single, cohesive ranking model.
- **Semantic Vector Search:** Implemented natural language search using SentenceTransformers and Qdrant.
- **Adaptive Taste Learning:** Designed a system that continuously updates user profiles based on ratings, watchlists, and interaction history.
- **Transparent Explainability:** Developed an attribution layer that translates mathematical scores into human-readable recommendation reasoning.
- **Production Architecture:** Integrated PostgreSQL, Redis, and Qdrant into a robust, Dockerized environment.
- **Scalable Service Design:** Built a FastAPI backend with strict separation of business logic, machine learning pipelines, and API routing.

---

## Screenshots

<table>
<tr>
<td width="50%">

**Home & Recommendations**
![Home Dashboard](Assets/Screenshot%202026-05-31%20224449.png)
*Personalised AI recommendations with match scores and reasoning*

</td>
<td width="50%">

**Semantic Search**
![Semantic Search](Assets/Screenshot%202026-05-31%20224733.png)
*Natural language movie discovery powered by vector embeddings*

</td>
</tr>
<tr>
<td width="50%">

**Movie Details**
![Movie Details](Assets/Screenshot%202026-05-31%20224558.png)
*Rich movie information with AI insights and similar movies*

</td>
<td width="50%">

**Taste Analytics**
![Taste Analytics](Assets/Screenshot%202026-05-29%20141152.png)
*AI-computed taste fingerprint with genre radar and engine weights*

</td>
</tr>
</table>

---

## System Architecture

![CineAI System Architecture](Assets/ChatGPT%20Image%20May%2031%2C%202026%2C%2010_04_44%20PM.png)

The platform is built on a clean layered architecture separating the frontend presentation layer, FastAPI backend, ML/AI pipeline, and data infrastructure — each independently scalable and maintainable.

---

## AI Recommendation Pipeline

![AI Recommendation Pipeline](Assets/ChatGPT%20Image%20May%2031%2C%202026%2C%2010_23_28%20PM.png)

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

## Core Capabilities

### Conversational Semantic Search
Break free from rigid keyword constraints. Search for movies exactly how you would describe them to a friend. We instantly encode your query into a 384-dimensional vector space to find the perfect semantic match.

> **"mind-bending thriller"** → *Inception, Memento, Shutter Island* <br/>
> **"movies about loneliness"** → *Her, Lost in Translation, Aftersun* <br/>
> **"emotional sci-fi about grief"** → *Annihilation, Arrival, Melancholia*

### Adaptive Hybrid Engine
Why rely on one algorithm when you can have an ensemble? CineAI dynamically fuses four distinct recommendation signals (Semantic, Content, Collaborative, and Popularity), automatically adjusting the mathematical weights to perfectly align with your unique cinematic taste.

### Transparent Explainability
No more "black box" suggestions. Every movie recommendation comes with clear, human-readable reasoning drawn directly from the underlying algorithmic score attributions.

> ✦ *Matches your deep appreciation for philosophical Sci-Fi* <br/>
> ✦ *Directed by Denis Villeneuve — a filmmaker you consistently rate highly* <br/>
> ✦ *Shares a similar emotional tone with movies you've rated 4.5+*

### Continuous Taste Learning
Your profile is a living, breathing entity. Every rating, watchlist addition, and dismissal continuously refines your:
- Genre and Director Affinities
- Mood Tag Preferences
- Semantic Centroid (the mathematical center of your favourite films)

### Intelligent Cold-Start Resolution
A seamless onboarding experience. Brand new users are greeted with a curated blend of trending and universally acclaimed titles. Once enough ratings are collected, the full machine learning pipeline seamlessly takes over.

---

## Platform Metrics

| Metric | Value |
|--------|-------|
| **Movies Indexed** | 2,992 |
| **Semantic Vectors** | 1,439 |
| **Embedding Dimensions** | 384 (all-MiniLM-L6-v2) |
| **Cache TTL** | 1 hour (Redis) |
| **API Endpoints** | 18 |
| **Database Tables** | 10 |
| **Hybrid Signals** | 4 |

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS | App Router, SSR, Responsive UI |
| **State Management** | Zustand, SWR | Client state, data fetching |
| **Backend** | FastAPI, Python 3.11 | Async REST API, ML orchestration |
| **Database** | PostgreSQL 16 (Supabase) | Primary relational data store |
| **Vector DB** | Qdrant | Semantic search, ANN retrieval |
| **Cache** | Redis (Upstash) | Recommendation caching, rate limiting |
| **Embeddings** | sentence-transformers | 384-dim dense movie vectors |
| **Collaborative** | scikit-surprise | SVD matrix factorisation |
| **Content Filtering**| scikit-learn | TF-IDF metadata similarity |
| **Data Provider** | TMDb API | Movie metadata, posters |
| **Infrastructure** | Docker Compose | Local container orchestration |
| **Security** | JWT + httpOnly cookies | Secure refresh-token authentication |

---

## Technical Challenges Solved

### Semantic Retrieval Without GPU
Running `all-MiniLM-L6-v2` fully on CPU with batch encoding and asynchronous Qdrant upserts. This approach completely eliminates the need for expensive GPU instances, allowing deployment on standard free-tier servers (e.g., 512MB RAM) without sacrificing latency.

### Hybrid Fusion with Explainability
Each of the four recommendation signals returns a normalised 0–1 score. The hybrid ranker fuses them with per-user learned weights, and the explainability layer attributes the dominant signal to generate human-readable reasons. This provides direct score attribution rather than post-hoc rationalisation.

### Adaptive Per-User Weights
Instead of applying global recommendation weights, each user's hybrid formula adapts using Exponential Moving Average (EMA) updates triggered by feedback actions. A user who consistently dismisses popularity-driven recommendations will see that signal's weight decrease automatically.

### Cold-Start Problem
Implemented a three-tier fallback mechanism: trending movies → genre-affinity fallback → full ML pipeline (which activates at 5+ ratings). This guarantees that no user ever sees an empty recommendation page.

### Vector Database on Free Tier
Qdrant's `indexing_threshold` is deliberately set to 20,000 vectors. Below this threshold, vectors are stored and searchable in O(n) mode without memory-intensive ANN indexing. This is perfectly functional at the current dataset scale and automatically upgrades to an HNSW index as the dataset grows.

### TMDb Access from Restricted Networks
External HTTPS connectivity issues were resolved by implementing a Cloudflare Worker proxy. This incurs zero additional cost while routing all TMDb API calls through a globally distributed edge network, ensuring high availability.

---

## Architecture Decisions

A key focus of this project was to avoid over-engineering while building a production-ready system. Here are the core technical decisions:

- **Why FastAPI?** For its native async support and extremely fast execution speed. Recommendations require gathering data from multiple sources concurrently (Qdrant, PostgreSQL, Redis). FastAPI handles these asynchronous I/O bound operations flawlessly while auto-generating our OpenAPI specs.
- **Why Qdrant instead of FAISS?** While FAISS is incredibly fast for local vector indexing, Qdrant is built as a complete vector database with native metadata filtering, a robust REST/gRPC API, and excellent Docker support, making it far superior for a web-service architecture.
- **Why PostgreSQL?** It is the most robust open-source relational database. We rely heavily on its JSONB support for storing complex user interactions, and standard relational constraints for ensuring data integrity across users, ratings, and watchlists.
- **Why Redis?** Movie popularity and the base recommendation algorithms are computationally heavy but change slowly. Redis caches the final recommendation payloads, reducing the 50ms pipeline generation time down to a 2ms cache hit for active users.
- **Why Sentence Transformers?** Specifically `all-MiniLM-L6-v2`. It produces incredibly dense 384-dimensional embeddings (compact enough to fit in RAM/VRAM) while matching the semantic quality of models 5x its size. It runs flawlessly on CPU in our Render deployment.
- **Why hybrid recommendations instead of keyword-only search?** Keyword searches fail when users don't know the exact terms (e.g., "movies like Inception but sadder"). By combining Semantic (meaning), Content (metadata), Collaborative (behavior), and Popularity (baseline), the engine captures the nuance of human taste that single-algorithm systems miss.

---

## Project Structure

A deeply decoupled layered architecture separating the Next.js presentation layer, FastAPI service backend, and ML pipeline.

```text
CineAI/
├── backend/                  # FastAPI Application & ML Pipeline
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── api/              # REST endpoints (auth, movies, search, recs)
│   │   ├── core/             # Database, Redis, security, exceptions
│   │   ├── ml/
│   │   │   ├── embeddings/   # Encoder, pipeline, user profile centroid
│   │   │   ├── explainability/# Score attribution → human reasoning
│   │   │   ├── feedback/     # Adaptive weight updater (EMA)
│   │   │   └── recommenders/ # Semantic, content, collaborative, hybrid
│   │   ├── models/           # SQLAlchemy ORM (10 tables)
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   └── services/         # Business logic layer
│   └── requirements.txt
├── frontend/                 # Next.js 14 Application
│   └── src/
│       ├── app/              # App Router & Pages
│       ├── components/       # Reusable UI components
│       ├── hooks/            # SWR data fetching hooks
│       ├── lib/              # Typed API client & utilities
│       └── store/            # Zustand global state
├── scripts/                  # Bootstrapping & seeding utilities
├── assets/                   # Documentation assets
└── docker-compose.yml        # Complete stack orchestration
```

---

## Future Roadmap 🚀

Our vision for the next evolution of CineAI:

- **Social & Collaborative:** User-to-user collaborative filtering, shared watchlists, and friend recommendations.
- **Conversational UI:** Multi-turn conversational movie discovery ("No, something a bit older than that").
- **Enriched Metadata:** Deep emotion, pacing, and tone metadata enrichment.
- **Advanced Embeddings:** Upgrading from `all-MiniLM-L6-v2` to `bge-large-en` for even richer semantic comprehension.
- **Experimentation:** Comprehensive A/B testing framework for evaluating recommendation strategies.
- **Mobile Experience:** Dedicated React Native application.
- **Real-time Updates:** WebSocket integration for instantaneous recommendation refreshes.

---

## License

This project is licensed under the **MIT License**.

See the [LICENSE](LICENSE) file for more details.

---

<div align="center">

*Engineered with FastAPI · Next.js · PostgreSQL · Redis · Qdrant · sentence-transformers*

</div>
