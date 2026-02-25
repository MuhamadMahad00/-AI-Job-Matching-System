# 🚀 AI Job Matching System — LangChain Edition

An AI-powered career matching platform that analyzes resumes and finds the best job fits using **LangChain v0.2+** with **LCEL chains**. Built with **FastAPI**, **Streamlit**, **FAISS VectorStore**, and **Groq LLM**.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📄 **Resume Parsing** | Extracts text from PDF and DOCX files automatically |
| 🤖 **AI Skill Extraction** | Uses LLM chain (Llama 3.3 via Groq) to identify skills from resume text |
| 🔍 **Semantic Job Search** | Matches resume against 100+ jobs using FAISS vector similarity search |
| 📊 **Smart Scoring** | Weighted score combining semantic similarity, skill overlap, and experience |
| 📝 **AI Career Report** | Generates a personalized career roadmap using LLM chain |
| ⬇️ **Report Download** | Export your AI-generated career report as a Markdown file |

---

## 🏗️ Architecture

The system uses a **chain-based pipeline** built with LangChain's **LCEL (LangChain Expression Language)** — clean, readable, and no unnecessary agents:

```
┌─────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                     │
│               (Upload Resume → View Results)             │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP POST /analyze
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                          │
│  1. Extract Text ─────────────── PyPDF / python-docx     │
│         │                                                │
│  2. Extract Skills ───────────── LCEL Chain               │
│         │                        (prompt | ChatGroq      │
│         │                         | JsonOutputParser)     │
│         │                                                │
│  3. Search Jobs ──────────────── FAISS VectorStore        │
│         │                        + HuggingFaceEmbeddings │
│         │                                                │
│  4. Score Matches ────────────── Python (weighted logic)  │
│         │                                                │
│  5. Career Report ────────────── LCEL Chain               │
│                                  (prompt | ChatGroq      │
│                                   | StrOutputParser)     │
└──────────────────────────────────────────────────────────┘
```

### Pipeline Steps

| Step | What Happens | Technology |
|---|---|---|
| **1. Text Extraction** | Reads PDF/DOCX and extracts raw text | PyPDF, python-docx |
| **2. Skill Extraction** | LLM identifies skills from resume text → returns structured JSON | LangChain LCEL: `ChatPromptTemplate` → `ChatGroq` → `JsonOutputParser` (Pydantic) |
| **3. Job Search** | Embeds resume text, searches FAISS index for similar jobs | LangChain `HuggingFaceEmbeddings` + `FAISS` VectorStore |
| **4. Match Scoring** | Calculates weighted score for each job match | Python (50% semantic + 30% skill overlap + 20% experience) |
| **5. Career Report** | LLM generates structured markdown career advice | LangChain LCEL: `ChatPromptTemplate` → `ChatGroq` → `StrOutputParser` |

---

## 🔗 LangChain Components Used

| Component | What It Replaces | Why |
|---|---|---|
| `ChatGroq` | Custom HTTP client (`requests.post` to Groq API) | Handles auth, retries, async natively |
| `ChatPromptTemplate` | Manual f-string prompts | Structured, reusable, template variables |
| `JsonOutputParser` + Pydantic | Manual `json.loads` + markdown stripping | Automatic JSON parsing with validation |
| `StrOutputParser` | Raw string extraction from API response | Clean text output from LLM |
| `HuggingFaceEmbeddings` | `SentenceTransformer(...)` direct usage | LangChain-compatible embedding interface |
| `FAISS` VectorStore | Manual `faiss.IndexFlatL2` + `add` / `search` / `write_index` | 3 function calls instead of 40 lines |
| **LCEL** (`prompt \| llm \| parser`) | Manual chaining of steps | Declarative, readable, async-native |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | LangChain v0.2+ (LCEL chains) |
| **Backend** | FastAPI (Python) |
| **Frontend** | Streamlit |
| **LLM** | Llama 3.3 70B via [Groq API](https://console.groq.com/) |
| **Embeddings** | `all-MiniLM-L6-v2` (via `langchain-huggingface`) |
| **Vector DB** | FAISS (via `langchain-community`) |
| **Resume Parsing** | PyPDF, python-docx |

---

## 📋 Prerequisites

- **Python 3.10+**
- **Groq API Key** — Get one free at [console.groq.com](https://console.groq.com/)

---

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd 2_project
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note**: The first run will automatically download the `all-MiniLM-L6-v2` embedding model (~80MB).

### 3. Configure Environment

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Add Job Data

Ensure `job_dataset.json` exists in the project root. It should contain an array of job objects:

```json
[
  {
    "JobID": 1,
    "Title": "Software Engineer",
    "Location": "Remote",
    "Responsibilities": ["Build APIs", "Write tests"],
    "Skills": ["python", "fastapi", "git"]
  }
]
```

### 5. Start the Backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at **http://127.0.0.1:8000**. On first run, it will build the FAISS index and save it to the `faiss_index/` folder. Subsequent starts load instantly from disk.

### 6. Start the Frontend

Open a **new terminal** and run:

```bash
streamlit run app.py
```

The UI will open at **http://localhost:8501**.

---

## 🖥️ Usage

1. Open the Streamlit app in your browser.
2. Upload your resume (PDF or DOCX format).
3. Click **"Analyze Resume & Find Matches"**.
4. View your **Top Job Matches** with match scores and missing skills.
5. Read your **AI Career Report** with personalized advice.
6. Click **"Download Report"** to save it as a Markdown file.

---

## 📡 API Reference

### `POST /analyze`

Analyzes a resume and returns job matches with a career report.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` — PDF or DOCX resume

**Response:**
```json
{
  "top_jobs": [
    {
      "job_id": 1,
      "title": "Senior Python Developer",
      "location": "Remote",
      "match_percentage": 92.5,
      "details": {
        "total_score": 92.5,
        "semantic_score": 95.0,
        "skill_match": 85.0,
        "missing_skills": ["Redis", "AWS"]
      }
    }
  ],
  "career_report": "# Career Analysis Report\n\n## Executive Summary\n..."
}
```

---

## 📁 Project Structure

```
2_project/
├── main.py              # FastAPI backend + LangChain chains + FAISS (all-in-one)
├── app.py               # Streamlit frontend UI
├── job_dataset.json     # Job database (JSON array)
├── faiss_index/         # FAISS vector index (auto-generated on first run)
├── requirements.txt     # Python dependencies
├── example_response.json# Sample API response for reference
├── .env                 # Environment variables (GROQ_API_KEY)
└── README.md            # This file
```

---

## � How It Works (Step-by-Step)

### Step 1: Resume Upload & Text Extraction

User uploads a PDF or DOCX file via Streamlit. The backend extracts raw text using `PyPDF` or `python-docx`.

### Step 2: Skill Extraction (LCEL Chain)

The resume text is passed to the **skill extraction chain**:

```python
skill_chain = (
    ChatPromptTemplate.from_messages([...])   # Structured prompt
    | ChatGroq(model="llama-3.3-70b-versatile")  # LLM call
    | JsonOutputParser(pydantic_object=SkillList) # Auto JSON parse
)

# Returns: {"skills": ["python", "fastapi", "machine learning", ...]}
```

The `JsonOutputParser` with Pydantic ensures the LLM always returns a valid JSON list — no manual markdown stripping needed.

### Step 3: Semantic Job Search (FAISS VectorStore)

The resume text is embedded using `HuggingFaceEmbeddings` and searched against the FAISS index:

```python
# Build (once, on first startup):
vectorstore = FAISS.from_texts(job_texts, embeddings)

# Search:
docs = vectorstore.similarity_search_with_score(resume_text, k=5)
```

LangChain's FAISS wrapper handles embedding, indexing, saving, and loading — replacing ~40 lines of manual FAISS code.

### Step 4: Match Scoring

Each job gets a weighted score combining three signals:

```
Final Score = (Semantic × 0.5) + (Skill Match × 0.3) + (Experience × 0.2)
```

| Component | Weight | How It's Calculated |
|---|---|---|
| Semantic Score | 50% | Vector similarity between resume and job embeddings |
| Skill Match | 30% | `overlapping_skills / total_job_skills` |
| Experience Score | 20% | Baseline factor (default: 0.8) |

It also identifies **missing skills** — skills the job requires that the resume doesn't have.

### Step 5: Career Report (LCEL Chain)

The **report chain** generates a structured markdown career report:

```python
report_chain = (
    ChatPromptTemplate.from_messages([...])  # Resume + matches + gaps
    | ChatGroq(model="llama-3.3-70b-versatile")
    | StrOutputParser()                       # Raw markdown text
)
```

The report includes:
1. **Executive Summary** — Overall profile assessment
2. **Top Job Fits** — Why the matched jobs are relevant
3. **Skill Gap Analysis** — Key skills to develop
4. **3-Month Learning Roadmap** — Actionable study plan
5. **Resume Tips** — Quick improvements

---

## 🧮 Scoring Algorithm

```
Final Score = (Semantic Score × 0.5) + (Skill Match × 0.3) + (Experience Score × 0.2)
```

| Component | Weight | Description |
|---|---|---|
| Semantic Score | 50% | Vector cosine similarity between resume and job embeddings |
| Skill Match | 30% | Percentage of job-required skills found in resume |
| Experience Score | 20% | Baseline experience factor (default: 0.8) |

---

## 🔧 Troubleshooting

| Issue | Solution |
|---|---|
| `GROQ_API_KEY not found` | Add your key to `.env` file |
| `Could not connect to backend` | Make sure `uvicorn` is running on port 8000 |
| `No matches found` | Ensure `job_dataset.json` exists and has data |
| `FAISS index folder not found` | Normal on first run — index builds automatically |
| `500 Internal Server Error` | Check the backend terminal for error details |
| LLM model errors | Update the model name in `main.py` to a current Groq model |

---

## 📦 Dependencies

```
fastapi                  # Web framework for the API
uvicorn                  # ASGI server
streamlit                # Frontend UI
faiss-cpu                # Vector similarity search
numpy                    # Numerical operations
python-multipart         # File upload handling
pypdf                    # PDF text extraction
python-docx              # DOCX text extraction
langchain-core           # LangChain core (prompts, parsers, LCEL)
langchain-groq           # ChatGroq LLM integration
langchain-huggingface    # HuggingFaceEmbeddings
langchain-community      # FAISS VectorStore
python-dotenv            # Environment variable loading
sentence-transformers    # Embedding model (all-MiniLM-L6-v2)
```

---

## 📄 License

This project is for educational and portfolio purposes.

---

**Built with ❤️ using LangChain, FastAPI, Streamlit, FAISS, and Groq AI**
