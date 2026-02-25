"""AI Job Matcher — LangChain version (single file, minimal design)."""

import os, json, logging, asyncio
from typing import List, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv
from pypdf import PdfReader
import docx

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ── Config ──────────────────────────────────────────────

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

JOBS_FILE = "job_dataset.json"
FAISS_DIR = "faiss_index"

# ── LLM + Embeddings ───────────────────────────────────

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=2048,
    api_key=os.getenv("GROQ_API_KEY"),
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# ── Chains (prompt | llm | parser) ─────────────────────

# Chain 1: Extract skills from resume
class SkillList(BaseModel):
    skills: List[str] = Field(description="Skills found in the resume")

skill_parser = JsonOutputParser(pydantic_object=SkillList)

skill_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "Extract all technical skills, soft skills, and tools from this resume. "
                   "Respond ONLY with valid JSON.\n{format_instructions}"),
        ("human", "{resume_text}"),
    ])
    | llm
    | skill_parser
)

# Chain 2: Generate career report
report_chain = (
    ChatPromptTemplate.from_messages([
        ("system", "You are an expert Career Coach. Generate a structured career report in Markdown."),
        ("human",
         "Resume Summary:\n{resume_text}\n\n"
         "Top Matched Jobs:\n{job_titles}\n\n"
         "Missing Skills:\n{missing_skills}\n\n"
         "Include: 1) Executive Summary  2) Top Job Fits  "
         "3) Skill Gap Analysis  4) 3-Month Learning Roadmap  5) Resume Tips"),
    ])
    | llm
    | StrOutputParser()
)

# ── Global state ───────────────────────────────────────

vectorstore: FAISS | None = None
jobs_list: List[Dict] = []

# ── Text extraction (PDF / DOCX) ──────────────────────

def extract_text(path: str, content_type: str) -> str:
    try:
        if path.endswith(".pdf") or "pdf" in content_type:
            with open(path, "rb") as f:
                return "\n".join(p.extract_text() or "" for p in PdfReader(f).pages).strip()
        elif path.endswith(".docx") or "wordprocessingml" in content_type:
            return "\n".join(p.text for p in docx.Document(path).paragraphs).strip()
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read file: {e}")

# ── FAISS VectorStore ─────────────────────────────────

def _job_text(job: Dict) -> str:
    return f"{job.get('Title','')}. {' '.join(job.get('Responsibilities',[]))}. Skills: {', '.join(job.get('Skills',[]))}"

async def build_vectorstore():
    global vectorstore, jobs_list
    if not os.path.exists(JOBS_FILE): return
    with open(JOBS_FILE) as f:
        jobs_list = json.load(f)[:100]
    texts = [_job_text(j) for j in jobs_list]
    metas = [{"index": i} for i in range(len(jobs_list))]
    loop = asyncio.get_event_loop()
    vectorstore = await loop.run_in_executor(None, lambda: FAISS.from_texts(texts, embeddings, metadatas=metas))
    vectorstore.save_local(FAISS_DIR)
    logger.info(f"Built FAISS index with {len(texts)} jobs.")

def load_vectorstore():
    global vectorstore, jobs_list
    vectorstore = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE) as f:
            jobs_list = json.load(f)[:100]
    logger.info("Loaded FAISS index from disk.")

# ── Scoring (business logic — unchanged) ──────────────

def calculate_score(resume_skills: List[str], job: Dict, semantic_score: float) -> Dict:
    job_skills = set(s.lower() for s in job.get("Skills", []))
    my_skills  = set(s.lower() for s in resume_skills)
    skill_score = len(my_skills & job_skills) / len(job_skills) if job_skills else 0
    final = (semantic_score * 0.5) + (skill_score * 0.3) + (0.8 * 0.2)
    return {
        "total_score":    round(final * 100, 1),
        "semantic_score": round(semantic_score * 100, 1),
        "skill_match":    round(skill_score * 100, 1),
        "missing_skills": list(job_skills - my_skills),
    }

# ── FastAPI ───────────────────────────────────────────

app = FastAPI(title="AI Job Matcher")

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.path.exists(FAISS_DIR):
        try: load_vectorstore()
        except: await build_vectorstore()
    else:
        await build_vectorstore()
    yield

app.router.lifespan_context = lifespan

@app.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    tmp = f"temp_{file.filename}"
    with open(tmp, "wb") as f:
        f.write(file.file.read())
    try:
        # 1) Extract text
        text = extract_text(tmp, file.content_type)
        if not text:
            raise HTTPException(400, "Could not extract text.")

        # 2) Extract skills via LLM chain
        result = await skill_chain.ainvoke({
            "resume_text": text[:4000],
            "format_instructions": skill_parser.get_format_instructions(),
        })
        skills = result.get("skills", [])

        # 3) Search similar jobs
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(
            None, lambda: vectorstore.similarity_search_with_score(text, k=5)
        ) if vectorstore else []

        # 4) Score matches
        matches, missing = [], set()
        for doc, dist in docs:
            idx = doc.metadata.get("index", -1)
            if 0 <= idx < len(jobs_list):
                job = jobs_list[idx]
                scores = calculate_score(skills, job, 1 / (1 + float(dist)))
                matches.append({
                    "job_id": job.get("JobID", "N/A"),
                    "title": job.get("Title", "Unknown"),
                    "location": job.get("Location", "Remote/Not Specified"),
                    "match_percentage": scores["total_score"],
                    "details": scores,
                })
                missing.update(scores["missing_skills"])
        matches.sort(key=lambda m: m["match_percentage"], reverse=True)

        # 5) Generate career report via LLM chain
        titles = [m["title"] for m in matches]
        report = await report_chain.ainvoke({
            "resume_text": text[:2000],
            "job_titles": json.dumps(titles),
            "missing_skills": ", ".join(list(missing)[:10]),
        })

        return {"top_jobs": matches, "career_report": report}

    except HTTPException: raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(500, str(e))
    finally:
        if os.path.exists(tmp): os.remove(tmp)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
