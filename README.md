# 🎬 CineAI

> An AI-powered movie recommendation platform that combines semantic search, hybrid recommendations, collaborative filtering, and user taste learning to deliver highly personalized movie discovery.

![Architecture Overview](images/architecture-overview.png)

## Overview

CineAI is a full-stack AI recommendation platform designed to help users discover movies based on meaning, themes, emotions, and personal preferences rather than relying solely on keywords or popularity.

Unlike traditional movie platforms, CineAI understands natural language queries such as:

* "movies about loneliness"
* "mind-bending thriller"
* "something like Interstellar"
* "emotional sci-fi movies"

Using vector embeddings, semantic retrieval, hybrid recommendation algorithms, and explainable recommendations, CineAI delivers highly relevant movie suggestions tailored to each user.

## Core Features

### AI Semantic Search

Search using natural language instead of exact keywords.

```text
movies about loneliness
mind-bending thriller
something like Inception
```

### Hybrid Recommendation Engine

Combines multiple recommendation strategies:

* Semantic Recommender
* Content-Based Recommender
* Collaborative Filtering
* Popularity Signals

### User Taste Learning

Continuously adapts recommendations using:

* Ratings
* Watchlist activity
* Recency weighting
* Negative preference modeling
* Taste clustering

### Explainable Recommendations

Every recommendation includes contextual explanations describing why it was generated.

### High Performance Architecture

Built using:

* Next.js
* FastAPI
* PostgreSQL
* Redis
* Qdrant
* Docker

## Tech Stack

| Layer            | Technology                 |
| ---------------- | -------------------------- |
| Frontend         | Next.js, React, TypeScript |
| Backend          | FastAPI, Python            |
| Database         | PostgreSQL                 |
| Cache            | Redis                      |
| Vector Database  | Qdrant                     |
| Embeddings       | all-MiniLM-L6-v2           |
| Containerization | Docker                     |
| State Management | Zustand                    |
| Styling          | Tailwind CSS + ShadCN      |
