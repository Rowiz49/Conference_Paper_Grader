Conference Paper Grader allows researchers to use their own local LLMs to review their papers against conference's checklists. Each question is answered with **Yes / Partial / No / NA**, accompanied by an explanation — giving reviewers a structured, consistent first-pass assessment.

![Python](https://img.shields.io/badge/Python-3.12+-blue?logo=python) ![Django](https://img.shields.io/badge/Django-6.x-green?logo=django) ![License](https://img.shields.io/badge/License-GPL--3.0-blue)

---

## Features

- 📋 **Conference management** — define conferences with custom evaluation question
- 🤖 **LLM-powered evaluation** — sends papers to any Ollama-compatible model for structured review
- 📊 **Visual results** — doughnut chart summarising the distribution of Yes / Partial / No / NA answers
- 🔒 **Privacy-first** — all processing runs locally through your own Ollama instance; no data leaves your infrastructure
- 🐳 **Docker-ready** — single-command deployment

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5, Python 3.12 |
| LLM client | [Ollama Python](https://github.com/ollama/ollama-python) |
| PDF parsing | [pymupdf4llm](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/) |
| Frontend | TailwindCSS v4, DaisyUI |
| Charts | Chart.js |
| Containerisation | Docker |

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) **or** Python 3.12+ with [uv](https://github.com/astral-sh/uv)
- A running [Ollama](https://ollama.com) instance with at least one model pulled (e.g. `ollama pull llama3`)

---

## Getting Started

### With Docker (recommended)

```bash
# Build the image
docker build -t conference-paper-grader .

# Run (host network is required to reach a local Ollama instance)
docker run --network=host conference-paper-grader
```

The app will be available at `http://localhost:8000`.

### Local development

```bash
# Install dependencies
uv sync

# Apply migrations
uv run python manage.py migrate

# Create a superuser to access the admin panel
uv run python manage.py createsuperuser

# Start the development server
uv run python manage.py tailwind dev
```

---

## Configuration

### 1. Set up a Conference and Questions

1. Go to `http://localhost:8000/admin`
2. Create a **Conference** with a name
3. Add **Questions** to the conference — each question has a position (order) and the question text the LLM will answer

### 2. Evaluate a Paper

1. Navigate to the home page
2. Select a conference
3. Enter your Ollama server URL (e.g. `http://localhost:11434`), model name (e.g. `llama3`), and optionally an API key
4. Upload a PDF paper
5. Submit — the app converts the PDF to Markdown, sends it to the LLM with the conference questions, and renders the structured evaluation

---

## How It Works

```
PDF upload → PyMuPDF → Markdown text
                              ↓
              Ollama prompt with conference questions
                              ↓
              Structured JSON response (position, question, rating, explanation)
                              ↓
              Results page with per-question badges + summary chart
```

The LLM is constrained to reply in a JSON schema derived from a Pydantic model, ensuring parseable, structured output. Ratings are validated and sorted by question position before rendering.
