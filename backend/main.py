"""
FormatIX FastAPI backend.

Endpoints:
  POST /upload-manuscript        — upload DOCX / PDF / TXT file
  POST /upload-text              — paste raw text
  POST /parse                    — extract raw text + sections
  POST /analyze-structure        — detect title, authors, abstract, citations
  POST /extract-rules            — compile formatting rules for selected style
  POST /analyze-corrections      — generate explainable correction list
  POST /format-document          — apply corrections and build DOCX
  POST /validate-citations       — cross-validate citations ↔ references
  POST /validate-format          — score formatting compliance
  GET  /download                 — download formatted DOCX
  GET  /job/{job_id}             — fetch full job state
  GET  /citation-styles          — list all available citation styles
  POST /format-citation          — generate a single formatted citation preview
  GET  /health                   — liveness check

Pipeline order per job:
  upload → parse → analyze-structure → extract-rules →
  analyze-corrections → format-document → validate-citations → validate-format
"""
import copy
import logging
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional, List

try:
    import pypandoc
    PANDOC_AVAILABLE = True
except ImportError:
    PANDOC_AVAILABLE = False

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, field_validator

from config import get_settings
from citation_styles import (
    CITATION_STYLES,
    STYLE_TITLE_MAP,
    generate_citation,
    get_formatting_rules,
    resolve_style_key,
)
from llm.groq_client import GroqClient
from agents.parser_agent import ParserAgent
from agents.structure_agent import StructureAgent
from agents.rule_agent import RuleExtractionAgent
from agents.format_agent import FormattingAgent
from agents.citation_engine import CitationEngine
from agents.validation_agent import ValidationAgent
from utils.docx_formatter import DocxFormatter
from utils.ieee_latex_generator import IEEELatexGenerator
from utils.latex_generator import LatexGenerator
from utils.template_scaffolder import TemplateScaffolder

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# App + config
# ─────────────────────────────────────────────────────────────────────────────

settings = get_settings()
settings.log_startup()

app = FastAPI(
    title="FormatIX API",
    version="1.0.0",
    description="Privacy-first AI manuscript formatting engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Storage directories
# ─────────────────────────────────────────────────────────────────────────────

UPLOAD_DIR = Path(settings.upload_dir)
OUTPUT_DIR = Path(settings.output_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".docx", ".pdf", ".txt", ".md"}

# ─────────────────────────────────────────────────────────────────────────────
# Job persistence helpers (resilience across server restarts)
# ─────────────────────────────────────────────────────────────────────────────

def _get_job_metadata_path(job_id: str) -> Path:
    """Get path to job metadata file."""
    return UPLOAD_DIR / job_id / "job_metadata.json"

def _save_job_metadata(job: dict) -> None:
    """Persist job metadata to disk (structure, rules, etc but not large parsed text)."""
    import json
    try:
        path = _get_job_metadata_path(job["job_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        # Save metadata but exclude large 'parsed' field
        metadata = {k: v for k, v in job.items() if k != "parsed"}
        path.write_text(json.dumps(metadata, default=str), encoding="utf-8")
    except Exception as e:
        log.warning("Failed to save job metadata: %s", e)

def _load_job_metadata(job_id: str) -> Optional[dict]:
    """Load job metadata from disk, returns None if no saved state."""
    import json
    try:
        path = _get_job_metadata_path(job_id)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning("Failed to load job metadata: %s", e)
    return None

# ─────────────────────────────────────────────────────────────────────────────
# LLM clients
# ─────────────────────────────────────────────────────────────────────────────

_groq = GroqClient(api_key=settings.groq_api_key, model=settings.groq_model_reasoning) \
        if settings.groq_api_key else None


async def llm_generate(
    mode: str,
    model: str,
    prompt: str,
    system: Optional[str] = None,
) -> str:
    """
    Unified LLM call - uses cloud mode (Groq) only.
    The mode parameter is kept for API compatibility but always uses cloud.
    """
    # Always use cloud mode - local Ollama is for display purposes only
    if _groq:
        return await _groq.generate(prompt=prompt, system=system, model=model)
    raise RuntimeError("GROQ_API_KEY not set - cloud mode required")


# ─────────────────────────────────────────────────────────────────────────────
# Agent singletons
# ─────────────────────────────────────────────────────────────────────────────

parser_agent     = ParserAgent()
structure_agent  = StructureAgent(llm_generate)
rule_agent       = RuleExtractionAgent(llm_generate)
format_agent     = FormattingAgent(llm_generate)
citation_engine  = CitationEngine()
validation_agent = ValidationAgent(llm_generate)

# ─────────────────────────────────────────────────────────────────────────────
# In-memory job store
# Replace with Redis / SQLite for production deployments.
# ─────────────────────────────────────────────────────────────────────────────

jobs: dict = {}


def _new_job(job_id: str, filename: Optional[str] = None) -> dict:
    return {
        "job_id":             job_id,
        "filename":           filename,
        "selected_style":     None,
        "parsed":             None,
        "structure":          None,
        "rules":              None,
        "corrections":        [],
        "formatted":          None,
        "formatted_structure": None,
        "citation_validation": None,
        "format_validation":  None,
        "output_path":        None,
        "tex_output_path":    None,
    }


def _require_job(job_id: str) -> dict:
    if job_id not in jobs:
        # Try to load from disk
        metadata = _load_job_metadata(job_id)
        if metadata:
            jobs[job_id] = metadata
            return metadata
        raise HTTPException(404, "Job not found. Upload a manuscript first.")
    return jobs[job_id]


def _require_field(job: dict, *fields: str) -> None:
    missing = [f for f in fields if not job.get(f)]
    if missing:
        step_map = {
            "parsed":    "/parse",
            "structure": "/analyze-structure",
            "rules":     "/extract-rules",
            "corrections": "/analyze-corrections",
        }
        hints = [step_map.get(f, f"/run-{f}") for f in missing]
        raise HTTPException(400, f"Missing: {missing}. Run {hints} first.")


def _norm_heading(text: str) -> str:
    """Normalise heading for comparison: lowercase, alphanumeric only."""
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


# ─────────────────────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────────────────────

class JobRequest(BaseModel):
    job_id: str
    use_cloud: bool = False


class ExtractRulesRequest(BaseModel):
    job_id: str
    style: str
    guidelines: Optional[str] = None
    use_cloud: bool = False


class FormatDocumentRequest(BaseModel):
    job_id: str
    accepted_corrections: List[dict] = []
    use_cloud: bool = False


class FormatCitationRequest(BaseModel):
    style: str
    source_type: str
    data: dict


class UploadTextRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def _not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text cannot be empty")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# Middleware: request size guard
# ─────────────────────────────────────────────────────────────────────────────

@app.middleware("http")
async def _limit_upload_size(request: Request, call_next):
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_file_size_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": f"File exceeds {settings.max_file_size_mb} MB limit"},
            )
    return await call_next(request)


# ─────────────────────────────────────────────────────────────────────────────
# Upload endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/upload-manuscript", summary="Upload a DOCX, PDF, or TXT manuscript")
async def upload_manuscript(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported format '{ext}'. Allowed: {ALLOWED_EXTENSIONS}")

    job_id   = str(uuid.uuid4())
    job_dir  = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or "document" + ext
    dest     = job_dir / filename

    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except OSError as e:
        raise HTTPException(500, f"Could not save file: {e}")

    jobs[job_id] = _new_job(job_id, filename)
    _save_job_metadata(jobs[job_id])
    log.info("Uploaded job=%s  file=%s", job_id, filename)
    return {"job_id": job_id, "filename": filename}


@app.post("/upload-text", summary="Submit raw pasted text")
async def upload_text(body: UploadTextRequest):
    job_id  = str(uuid.uuid4())
    job_dir = UPLOAD_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    filename = "pasted_text.txt"
    dest     = job_dir / filename

    try:
        dest.write_text(body.text, encoding="utf-8")
    except OSError as e:
        raise HTTPException(500, f"Could not save text: {e}")

    jobs[job_id] = _new_job(job_id, filename)
    _save_job_metadata(jobs[job_id])
    log.info("Uploaded text job=%s  chars=%d", job_id, len(body.text))
    return {"job_id": job_id, "filename": filename}


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/parse", summary="Extract raw text and sections from the uploaded file")
async def parse(body: JobRequest):
    job = _require_job(body.job_id)
    path = UPLOAD_DIR / body.job_id / job["filename"]
    if not path.exists():
        raise HTTPException(404, "Upload file not found — did the server restart?")
    try:
        parsed = parser_agent.parse(str(path))
        job["parsed"] = parsed
        # Save raw_sections at job level for persistence (not nested in parsed)
        job["raw_sections"] = parsed.get("raw_sections", [])
        _save_job_metadata(job)
        return {
            "job_id":        body.job_id,
            "text_preview":  (parsed.get("text") or "")[:300],
            "section_count": len(parsed.get("raw_sections", [])),
            "char_count":    len(parsed.get("text") or ""),
        }
    except Exception as e:
        log.exception("Parse failed job=%s", body.job_id)
        raise HTTPException(500, str(e))


@app.post("/analyze-structure", summary="Detect title, authors, abstract, citations, and sections")
async def analyze_structure(body: JobRequest):
    job = _require_job(body.job_id)
    
    # If parsed is missing but raw_sections exist, reconstruct parsed dict
    if "parsed" not in job and "raw_sections" in job:
        job["parsed"] = {
            "type": "parsed_document",
            "text": "",  # We don't have the full text, but structures don't strictly need it
            "raw_sections": job["raw_sections"],
        }
    
    _require_field(job, "parsed")
    model = settings.groq_model_fast if body.use_cloud else settings.ollama_model_fast
    try:
        structure = await structure_agent.analyze(
            job["parsed"],
            use_cloud=body.use_cloud,
            model_fast=model,
        )
        job["structure"] = structure
        _save_job_metadata(job)
        log.info("Structure done job=%s  sections=%d  refs=%d",
                 body.job_id, len(structure.get("sections", [])), len(structure.get("references", [])))
        return structure
    except Exception as e:
        log.exception("Structure analysis failed job=%s", body.job_id)
        raise HTTPException(500, str(e))


@app.post("/extract-rules", summary="Compile formatting rules for the selected style")
async def extract_rules(body: ExtractRulesRequest):
    # Allow a "preview" sentinel so the UI can fetch rules before upload
    if body.job_id not in jobs:
        if body.job_id in ("preview", ""):
            jobs[body.job_id] = _new_job(body.job_id)
        else:
            raise HTTPException(404, "Job not found. Upload a manuscript first.")

    job = jobs[body.job_id]

    try:
        style_key = resolve_style_key(body.style)
    except ValueError as e:
        raise HTTPException(400, str(e))

    job["selected_style"] = style_key
    model = settings.groq_model_fast if body.use_cloud else settings.ollama_model_fast

    try:
        rules = await rule_agent.extract(
            style=style_key,
            guidelines_text=body.guidelines or "",
            use_cloud=body.use_cloud,
            model_fast=model,
        )
        # Merge document-level citation-style metadata (from citation_styles.py)
        # into the rule dict — keeps citation_style as a plain string, not nested dict
        fmt_rules = get_formatting_rules(style_key)
        rules["citation_style_meta"] = fmt_rules   # full metadata for UI
        # Ensure citation_style stays as the plain string RuleAgent produced
        rules.setdefault("citation_style", fmt_rules.get("citation_type", "author-year"))

        job["rules"] = rules
        _save_job_metadata(job)
        log.info("Rules extracted job=%s  style=%s  use_cloud=%s", body.job_id, style_key, body.use_cloud)
        return rules
    except Exception as e:
        log.exception("Rule extraction failed job=%s", body.job_id)
        raise HTTPException(500, str(e))


@app.post("/analyze-corrections", summary="Generate an explainable list of formatting corrections")
async def analyze_corrections(body: JobRequest):
    job = _require_job(body.job_id)
    _require_field(job, "structure", "rules")
    model = settings.groq_model_reasoning if body.use_cloud else settings.ollama_model_reasoning
    try:
        corrections = await format_agent.analyze_corrections(
            job["structure"],
            job["rules"],
            use_cloud=body.use_cloud,
            model_reasoning=model,
        )
        job["corrections"] = corrections
        _save_job_metadata(job)
        log.info("Corrections done job=%s  count=%d", body.job_id, len(corrections))
        return {"corrections": corrections}
    except Exception as e:
        log.exception("Corrections failed job=%s", body.job_id)
        raise HTTPException(500, str(e))


@app.post("/format-document", summary="Apply corrections and build the formatted DOCX + LaTeX")
async def format_document(body: FormatDocumentRequest):
    job = _require_job(body.job_id)
    _require_field(job, "structure", "rules")

    # Use explicitly accepted corrections, or fall back to all generated ones
    accepted = body.accepted_corrections or job.get("corrections", [])

    try:
        # Deep-copy so we don't mutate the stored structure
        structure = copy.deepcopy(job["structure"])

        # ── CONTENT PRESERVATION: Ensure sections have actual content ──
        # If raw_sections exist and have better structure, use them
        if job.get("raw_sections"):
            raw_sections = job.get("raw_sections", [])
            # Check if current sections are mostly empty
            current_with_content = [s for s in structure.get("sections", []) if (s.get("content") or "").strip()]
            raw_with_content = [s for s in raw_sections if (s.get("content") or "").strip()]
            
            if not current_with_content and raw_with_content:
                # Sections were lost, rebuild from raw_sections
                log.info("Rebuilding all sections from raw_sections (structure sections had no content)")
                structure["sections"] = [
                    {
                        "heading": sec.get("heading", "Untitled"),
                        "level": sec.get("level", 1),
                        "content": sec.get("content", ""),
                        "word_count": len(sec.get("content", "").split()),
                    }
                    for sec in raw_sections
                ]
            elif len(raw_with_content) > len(current_with_content):
                # Raw sections have more content, prefer them
                log.info("Using raw_sections (has more section content)")
                structure["sections"] = [
                    {
                        "heading": sec.get("heading", "Untitled"),
                        "level": sec.get("level", 1),
                        "content": sec.get("content", ""),
                        "word_count": len(sec.get("content", "").split()),
                    }
                    for sec in raw_sections
                ]

        # Apply accepted text corrections to abstract and section content
        for c in accepted:
            orig   = str(c.get("original", "")).strip()
            change = str(c.get("change", "")).strip()
            if not orig or not change or orig == change:
                continue
            if structure.get("abstract"):
                structure["abstract"] = structure["abstract"].replace(orig, change)
            for sec in structure.get("sections", []):
                if sec.get("content"):
                    sec["content"] = sec["content"].replace(orig, change)

        job["formatted_structure"] = structure

        rules       = job["rules"]
        style_lower = str(job.get("selected_style") or rules.get("style", "apa")).lower()

        # Ensure document title is set (for broken/incomplete input)
        if not (structure.get("title") or "").strip():
            structure["title"] = "Untitled"

        # Ensure sections list is present and non-empty
        if not structure.get("sections"):
            structure["sections"] = []
        
        # Log section summary for debugging
        sections_with_content = [s for s in structure.get("sections", []) if (s.get("content") or "").strip()]
        log.info("Format document job=%s  sections=%d  with_content=%d", 
                 body.job_id, len(structure.get("sections", [])), len(sections_with_content))

        out_dir     = OUTPUT_DIR / body.job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path    = out_dir / "formatted.docx"
        tex_path    = out_dir / "formatted.tex"

        # ── Build DOCX ────────────────────────────────────────────────────────
        formatter = DocxFormatter(rules)
        formatter.create_document(
            title       = structure.get("title", "Untitled"),
            authors     = structure.get("authors", []),
            abstract    = structure.get("abstract", ""),
            sections    = structure.get("sections", []),
            references  = structure.get("references", []),
            output_path = str(out_path),
            keywords    = structure.get("keywords", []),
            affiliation = structure.get("affiliation"),
            course_info = structure.get("course_info"),
        )

        # ── Build LaTeX ───────────────────────────────────────────────────────
        if style_lower == "ieee":
            tex_gen = IEEELatexGenerator(llm_generate_fn=llm_generate)
            tex_gen.generate(structure, output_path=str(tex_path))
        else:
            tex_gen = LatexGenerator(style=style_lower)
            tex_gen.generate(structure, output_path=str(tex_path))

        # ── Prefer DOCX from LaTeX via pandoc (matches LaTeX output) ───────────
        docx_from_latex = out_dir / "formatted_from_latex.docx"
        if PANDOC_AVAILABLE:
            try:
                latex_content = tex_path.read_text(encoding="utf-8")
                docx_output = pypandoc.convert_text(
                    latex_content,
                    "docx",
                    format="latex",
                    outputfile=str(docx_from_latex),
                )
                if docx_from_latex.exists():
                    shutil.move(str(docx_from_latex), str(out_path))
                    job["formatted"] = {"status": "completed", "method": "pandoc-latex-to-docx"}
                    log.info("DOCX generated from LaTeX via pypandoc job=%s", body.job_id)
            except Exception as e:
                log.info("Pandoc conversion failed: %s — serving python-docx output", e)
                job["formatted"] = job.get("formatted") or {"status": "completed", "method": "python-docx"}
        else:
            log.info("Pandoc not available — serving python-docx output")
            job["formatted"] = job.get("formatted") or {"status": "completed", "method": "python-docx"}

        job["output_path"]     = str(out_path)
        job["tex_output_path"] = str(tex_path)
        _save_job_metadata(job)

        log.info("DOCX + LaTeX built job=%s  style=%s", body.job_id, style_lower)
        return {
            "formatted":      job["formatted"],
            "corrections":    accepted,
            "output_path":    str(out_path),
            "tex_output_path": str(tex_path),
            "download_url":   f"/download?job_id={body.job_id}",
            "latex_url":      f"/format-latex?job_id={body.job_id}",
        }
    except Exception as e:
        log.exception("Format document failed job=%s", body.job_id)
        raise HTTPException(500, str(e))


@app.post("/validate-citations", summary="Cross-validate in-text citations against the reference list")
async def validate_citations(body: JobRequest):
    job = _require_job(body.job_id)
    _require_field(job, "structure")

    structure = job["structure"]
    raw_text  = (job.get("parsed") or {}).get("text", "")

    # Re-create engine with the correct citation style from extracted rules
    style = (job.get("rules") or {}).get("citation_style", "author-year")
    engine = CitationEngine(citation_style=style)

    result = engine.validate(structure, raw_text=raw_text)
    job["citation_validation"] = result
    _save_job_metadata(job)
    log.info("Citation validation job=%s  match_rate=%.2f", body.job_id, result.get("match_rate", 0))
    return result


@app.post("/validate-format", summary="Score formatting compliance and list issues")
async def validate_format(body: JobRequest):
    job = _require_job(body.job_id)
    _require_field(job, "structure", "rules")

    citation_result = job.get("citation_validation") or {}
    model = settings.groq_model_reasoning if body.use_cloud else settings.ollama_model_reasoning

    try:
        result = await validation_agent.validate(
            job["structure"],
            job["rules"],
            citation_result,
            use_cloud=body.use_cloud,
            model_reasoning=model,
        )
        job["format_validation"] = result
        _save_job_metadata(job)
        log.info("Validation done job=%s  score=%d", body.job_id, result.get("formatting_score", 0))
        return result
    except Exception as e:
        log.exception("Validation failed job=%s", body.job_id)
        raise HTTPException(500, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Download + job state
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/download", summary="Download the formatted DOCX file")
async def download(job_id: str, filename: str = "formatted.docx"):
    # Sanitise job_id
    if not job_id.replace("-", "").isalnum() or len(job_id) > 64:
        raise HTTPException(400, "Invalid job_id")
    job = _require_job(job_id)
    out_path = job.get("output_path")
    if not out_path or not Path(out_path).exists():
        raise HTTPException(404, "Formatted file not ready. Run /format-document first.")
    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename or "formatted.docx",
    )


@app.get("/download-latex", summary="Download the formatted .tex file")
async def download_latex(job_id: str):
    if not job_id.replace("-", "").isalnum() or len(job_id) > 64:
        raise HTTPException(400, "Invalid job_id")
    job = _require_job(job_id)
    tex_path = job.get("tex_output_path")
    if not tex_path or not Path(tex_path).exists():
        raise HTTPException(404, "LaTeX file not ready. Run /format-document first.")
    return FileResponse(
        tex_path,
        media_type="application/x-tex",
        filename="formatted.tex",
    )


@app.get("/format-latex", summary="Get the LaTeX source as a string (for preview)")
async def get_latex(job_id: str):
    if not job_id.replace("-", "").isalnum() or len(job_id) > 64:
        raise HTTPException(400, "Invalid job_id")
    job = _require_job(job_id)
    tex_path = job.get("tex_output_path")
    if not tex_path or not Path(tex_path).exists():
        raise HTTPException(404, "LaTeX file not ready. Run /format-document first.")
    return {"latex": Path(tex_path).read_text(encoding="utf-8")}


@app.get("/job/{job_id}", summary="Get full job state")
async def get_job(job_id: str, include_parsed: bool = False):
    job = _require_job(job_id)
    # By default exclude parsed (can be large); Compare page can request it via ?include_parsed=true
    summary = dict(job) if include_parsed else {k: v for k, v in job.items() if k != "parsed"}
    if job.get("structure") and "structure_summary" not in summary:
        summary["structure_summary"] = {
            "title":           job["structure"].get("title", ""),
            "author_count":    len(job["structure"].get("authors", [])),
            "section_count":   len(job["structure"].get("sections", [])),
            "reference_count": len(job["structure"].get("references", [])),
            "citation_format": job["structure"].get("citation_format", "unknown"),
            "word_count":      job["structure"].get("word_count_total", 0),
        }
    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Citation style endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/citation-styles", summary="List all available citation styles")
async def list_citation_styles():
    result = {
        key: {
            "name":          data["name"],
            "category":      data["category"],
            "layout":        data["layout"],
            "citation_type": data["citation_type"],
            "in_text":       data["in_text"],
            "formatting":    data["formatting"],
        }
        for key, data in CITATION_STYLES.items()
    }
    return {"styles": result, "title_map": STYLE_TITLE_MAP}


@app.post("/format-citation", summary="Generate a single formatted citation for preview")
async def format_citation_endpoint(body: FormatCitationRequest):
    """
    Generate a citation string for the given style and source data.
    Used by the UI for live preview when the user clicks a style card.

    Example body:
    {
        "style": "APA 7th Edition",
        "source_type": "journal",
        "data": {
            "authors": "A. Kumar and B. Patel",
            "year": "2024",
            "title": "Deep Learning for NLP",
            "journal": "IEEE Trans. Neural Networks",
            "volume": "34", "pages": "123-130"
        }
    }
    """
    try:
        citation   = generate_citation(style=body.style, source_type=body.source_type, data=body.data)
        fmt_rules  = get_formatting_rules(body.style)
        return {
            "citation":         citation,
            "style_key":        fmt_rules["style_key"],
            "style_name":       fmt_rules["name"],
            "citation_type":    fmt_rules["citation_type"],
            "in_text_format":   fmt_rules["in_text"],
            "formatting_rules": fmt_rules["formatting"],
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log.exception("format-citation failed")
        raise HTTPException(500, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health", summary="Liveness check")
async def health():
    return {
        "status":     "ok",
        "ai_mode":    settings.ai_mode,
        "use_cloud":  settings.use_cloud,
        "active_models": {
            "fast":      settings.active_model_fast,
            "reasoning": settings.active_model_reasoning,
        },
        "job_count": len(jobs),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )