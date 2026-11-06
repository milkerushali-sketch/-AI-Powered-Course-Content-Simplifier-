# AI-Powered Course Content Simplifier

**Problem Statement #19 · IBM University Engagement Project**

Powered by **IBM Granite** (`ibm/granite-3-8b-instruct`) via **IBM watsonx.ai**

---

## What It Does

Students often struggle with academic materials written above their proficiency level. This app uses IBM Granite to automatically transform any educational content into learner-appropriate language — in a single AI call — for three levels:

| Level | Target Learner |
|---|---|
| **Beginner** | Age 10–12, completely new to the topic |
| **Intermediate** | Age 15–17, some subject knowledge |
| **Advanced** | University student, technically accurate explanation |

For any piece of academic content the AI returns **six structured sections**:

| Section | Description |
|---|---|
| Simple Definition | Core concept defined in plain language |
| Easy Explanation | Numbered step-by-step breakdown |
| Real-Life Example | Concrete, relatable analogy or scenario |
| Important Exam Points | 5–7 key bullet facts for revision |
| Short Summary | 3–5 sentence concise overview |
| Difficult Words | Glossary of technical terms with simple definitions |

**Bonus:** MCQ quiz generation (5 questions), revision question generation (5 questions), downloadable results, and session history.

---

## App Pages

| Page | What You Can Do |
|---|---|
| **Home** | Quick-start — paste or upload content and simplify in one click |
| **Simplify** | Full input interface with three tabs: Paste Text · Upload File · Sample Passage |
| **Study Materials** | Browse the Kaggle dataset passages and compare AI output with real student summaries |
| **Quiz** | Generate and take an interactive MCQ quiz from any content |
| **History** | Review all past simplifications from the current session; download as text |
| **About** | Project info, technology stack, and credential setup guide |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/milkerushali-sketch/-AI-Powered-Course-Content-Simplifier-.git
cd -AI-Powered-Course-Content-Simplifier-
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

Or using the npm helper script (requires Node.js):

```bash
npm run install:py
```

### 3. Configure IBM credentials

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in your IBM Cloud credentials:

```
WATSONX_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
```

> **Where to get credentials**
> - **API Key:** [cloud.ibm.com/iam/apikeys](https://cloud.ibm.com/iam/apikeys) → Create an IBM Cloud API key
> - **Project ID:** [dataplatform.cloud.ibm.com/projects](https://dataplatform.cloud.ibm.com/projects) → Open your project → Manage tab

### 4. Run the app

```bash
python -m streamlit run app.py
```

Or:

```bash
npm run dev
```

Open your browser at **http://localhost:8501**

---

## Demo Mode

If IBM credentials are not configured, the app automatically runs in **Demo Mode**. You will see realistic, content-aware placeholder responses that show the full structure of the output. Every page and feature works identically — no credentials needed to explore the UI.

---

## Project Files

```
course-simplifier/
├── app.py              ← Streamlit frontend — all 6 pages, UI, session state
├── granite.py          ← IBM Granite / watsonx.ai integration
│                         IAM token caching, combined prompt, demo mode
├── dataset.py          ← Kaggle CommonLit dataset processing
│                         CSV loading, passage extraction, student summaries
├── requirements.txt    ← Python dependencies
├── .env.example        ← Credentials template (safe to commit)
├── .env                ← Your actual credentials (DO NOT commit — gitignored)
├── test_integration.py ← Integration tests for granite.py and dataset.py
└── README.md           ← This file
```

---

## Architecture

```
Browser
  │
  ▼
Streamlit UI  (app.py)
  │
  ├── granite.py
  │     ├── GET  https://iam.cloud.ibm.com/identity/token   ← IAM auth (cached ~60 min)
  │     └── POST {WATSONX_URL}/ml/v1/text/generation        ← IBM Granite inference
  │
  └── dataset.py
        ├── kagglehub  ← auto-download CommonLit competition data
        └── pandas     ← CSV parsing, passage/summary retrieval
```

---

## IBM Granite Integration Details

- **Model:** `ibm/granite-3-8b-instruct`
- **API version:** `2024-05-31`
- **Endpoint:** `POST {WATSONX_URL}/ml/v1/text/generation`
- **Decoding:** greedy, `repetition_penalty=1.05`, `stop_sequences=["---END---"]`
- **Single combined prompt:** all 6 simplification sections are requested in one API call (not 6 separate calls) — reduces latency and token usage
- **IAM token caching:** the bearer token is cached for its ~60-minute lifetime; only one `/identity/token` call per session
- **Lazy credential loading:** credentials are read inside functions, not at import time, so `load_dotenv()` always runs first

---

## Kaggle Dataset Integration

This app integrates with the **CommonLit – Evaluate Student Summaries** competition dataset.

### Built-in sample passages (no Kaggle account needed)

Five passages are built in and always available:

1. Photosynthesis
2. Newton's Laws of Motion
3. The Water Cycle
4. DNA and Genetics
5. Supply and Demand in Economics

### Loading the full Kaggle dataset

**Option A — Auto-download via kagglehub (sidebar button)**

Requirements:
- Kaggle credentials at `~/.kaggle/kaggle.json` OR environment variables `KAGGLE_USERNAME` and `KAGGLE_KEY`
- Competition rules accepted at [kaggle.com/c/commonlit-evaluate-student-summaries](https://www.kaggle.com/c/commonlit-evaluate-student-summaries)

**Option B — Manual upload (sidebar file uploaders)**

1. Download `prompts_train.csv` and `summaries_train.csv` from the Kaggle competition page
2. Upload each file using the sidebar file uploaders in the app

After loading, the **Study Materials** page lets you select any passage and compare the AI simplification with real student-written summaries from the dataset.

---

## Technologies Used

| Technology | Version | Role |
|---|---|---|
| IBM Granite | `ibm/granite-3-8b-instruct` | Foundation LLM for simplification, MCQ, and revision generation |
| IBM watsonx.ai | REST API `2024-05-31` | Model inference platform |
| IBM Cloud | — | Cloud infrastructure and IAM authentication |
| Streamlit | `>=1.32.0` | Web UI framework |
| Python | `3.11` | Backend logic |
| pandas | `>=2.0.0` | CSV processing and dataset handling |
| pypdf | `>=4.0.0` | PDF text extraction |
| python-dotenv | `>=1.0.0` | `.env` file credential loading |
| kagglehub | `>=0.3.0` | Kaggle dataset auto-download |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `No module named streamlit` | Run `pip install -r requirements.txt` |
| IBM Granite API 401 Unauthorized | Check `WATSONX_API_KEY` in your `.env` file |
| IBM Granite API 404 Not Found | Check `WATSONX_PROJECT_ID` and `GRANITE_MODEL_ID` |
| App shows Demo Mode but credentials are set | Ensure `.env` exists (not just `.env.example`) and credentials don't start with `your_` |
| PDF upload fails | Ensure `pypdf>=4.0.0` is installed: `pip install pypdf` |
| Kaggle download fails | Accept competition rules on Kaggle and check `~/.kaggle/kaggle.json` exists |
| App not opening in browser | Navigate to [http://localhost:8501](http://localhost:8501) manually |
| Port 8501 already in use | Streamlit will use 8502 — check the terminal output for the exact URL |

---

## .gitignore — Key Exclusions

`.env`, `venv/`, `__pycache__/`, `*.pptx`, `node_modules/`, `*.log`

The `.env` file is never committed. Use `.env.example` as the template.

---

*Built with IBM Granite · IBM watsonx.ai · Streamlit · Problem Statement #19*
