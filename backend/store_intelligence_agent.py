"""
Store Intelligence Agent

Uses a pre-configured DigitalOcean Knowledge Base for RAG:
- KB is created manually via DO Control Panel (with OpenSearch + embedding model)
- Queries the KB retrieve API for semantic + lexical hybrid search
- Uses Gradient AI llama3-8b-instruct for answer generation
- Falls back to SQL search when KB is not configured or unavailable
"""

import os
import io
import uuid
import logging
from typing import List, Optional

import httpx
from openai import OpenAI
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Gradient AI config
GRADIENT_API_KEY = os.getenv("GRADIENT_API_KEY") or os.getenv("GRADIENT_AI_MODEL_KEY")
GRADIENT_MODEL = os.getenv("GRADIENT_MODEL") or os.getenv("GRADIENT_AI_MODELNAME", "llama3-8b-instruct")
GRADIENT_BASE_URL = os.getenv("GRADIENT_BASE_URL", "https://inference.do-ai.run/v1/")

# DigitalOcean API config
DO_API_TOKEN = os.getenv("DIGITALOCEAN_API_TOKEN")

# Knowledge Base retrieve endpoint — set from DO Control Panel
# Format: https://kbaas.do-ai.run/v1/<kb-uuid>/retrieve
KB_ENDPOINT = os.getenv("DO_KB_ENDPOINT", "")

# Spaces config
SPACES_BUCKET = os.getenv("DO_SPACES_BUCKET", "1donsspaces")
SPACES_REGION = os.getenv("DO_SPACES_REGION", "nyc3")

# RAG prompt templates
RAG_SYSTEM_PROMPT = """You are a helpful Store Intelligence assistant. Answer questions about products based ONLY on the provided context. If the context doesn't contain relevant information, say so. Always be accurate and cite which document the information comes from."""

RAG_USER_PROMPT = """Based on the following product documentation:
{context}
---
Question: {question}
Provide a helpful, accurate answer based on the documentation above."""


def _do_headers() -> dict:
    return {
        "Authorization": f"Bearer {DO_API_TOKEN}",
        "Content-Type": "application/json",
    }


def get_gradient_client() -> OpenAI:
    return OpenAI(api_key=GRADIENT_API_KEY, base_url=GRADIENT_BASE_URL, timeout=120.0)


# ---------------------------------------------------------------------------
# KB Retrieve API
# ---------------------------------------------------------------------------

async def kb_retrieve(question: str, num_results: int = 5) -> List[dict]:
    """Query the DO Knowledge Base retrieve API."""
    if not KB_ENDPOINT or not DO_API_TOKEN:
        return []

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                KB_ENDPOINT,
                headers=_do_headers(),
                json={
                    "query": question,
                    "num_results": num_results,
                    "alpha": 0.5,
                },
            )
            resp.raise_for_status()
            results = resp.json().get("results", [])
            logger.info(f"KB retrieve returned {len(results)} results")
            return [
                {
                    "chunk_id": str(i),
                    "document_id": r.get("metadata", {}).get("item_name", ""),
                    "filename": r.get("metadata", {}).get("item_name", "unknown").split("/")[-1],
                    "content": r.get("text_content", ""),
                    "score": 0.9,
                }
                for i, r in enumerate(results)
            ]
    except Exception as e:
        logger.warning(f"KB retrieve failed: {e}")
        return []


# ---------------------------------------------------------------------------
# KB health / details (for status page)
# ---------------------------------------------------------------------------

async def get_index_health() -> str:
    """Return KB health based on whether retrieve endpoint is reachable."""
    if not KB_ENDPOINT or not DO_API_TOKEN:
        return "red"
    try:
        # Quick test query to see if KB responds
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                KB_ENDPOINT,
                headers=_do_headers(),
                json={"query": "test", "num_results": 1, "alpha": 0.5},
            )
            if resp.status_code == 200:
                return "green"
            return "yellow"
    except Exception:
        return "red"


async def get_kb_details() -> dict:
    """Return KB info for the status page."""
    # Extract UUID from endpoint URL if available
    kb_uuid = None
    if KB_ENDPOINT:
        # URL format: https://kbaas.do-ai.run/v1/<uuid>/retrieve
        parts = KB_ENDPOINT.rstrip("/").split("/")
        if len(parts) >= 2:
            kb_uuid = parts[-2]

    health = await get_index_health()
    status = "active" if health == "green" else ("provisioning" if health == "yellow" else "not_configured")

    return {
        "uuid": kb_uuid,
        "status": status,
        "name": "store-intelligence",
        "spaces_bucket": SPACES_BUCKET,
        "spaces_region": SPACES_REGION,
        "embedding_model": "GTE Large v1.5",
    }


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text(file_content: bytes, file_type: str) -> str:
    file_type = file_type.lower().lstrip(".")
    if file_type == "pdf":
        return _extract_pdf(file_content)
    elif file_type in ("txt", "md"):
        return file_content.decode("utf-8", errors="replace")
    elif file_type == "csv":
        return file_content.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_content: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_content))
        return "\n\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise ValueError(f"Failed to extract text from PDF: {e}")


# ---------------------------------------------------------------------------
# Chunking (for SQL fallback)
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)


def chunk_text(text: str, target_tokens: int = 750, overlap_tokens: int = 100) -> List[dict]:
    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks, current_parts, current_count = [], [], 0
    max_tokens = 1000

    def _flush():
        nonlocal current_parts, current_count
        if not current_parts:
            return
        content = "\n\n".join(current_parts)
        chunks.append({"content": content, "token_count": _estimate_tokens(content), "chunk_index": len(chunks)})
        overlap_parts, oc = [], 0
        for part in reversed(current_parts):
            pt = _estimate_tokens(part)
            if oc + pt > overlap_tokens:
                break
            overlap_parts.insert(0, part)
            oc += pt
        current_parts, current_count = overlap_parts, oc

    for para in paragraphs:
        pt = _estimate_tokens(para)
        if pt > max_tokens:
            import re
            for s in re.split(r'(?<=[.!?])\s+', para):
                st = _estimate_tokens(s)
                if current_count + st > max_tokens:
                    _flush()
                current_parts.append(s)
                current_count += st
            continue
        if current_count + pt > max_tokens:
            _flush()
        current_parts.append(para)
        current_count += pt

    if current_parts:
        content = "\n\n".join(current_parts)
        chunks.append({"content": content, "token_count": _estimate_tokens(content), "chunk_index": len(chunks)})
    return chunks


# ---------------------------------------------------------------------------
# SQL fallback search
# ---------------------------------------------------------------------------

def _sql_fallback_search(question: str, db: Session, k: int = 5) -> List[dict]:
    from models import DocumentChunk, Document
    from sqlalchemy import or_, and_

    keywords = [w for w in question.lower().split() if len(w) > 2]
    if not keywords:
        keywords = question.lower().split()

    stop_words = {"the", "and", "for", "are", "but", "not", "you", "all",
                  "can", "had", "her", "was", "one", "our", "out", "has",
                  "what", "whats", "how", "who", "when", "where", "why",
                  "this", "that", "with", "from", "they", "been", "have",
                  "its", "will", "would", "could", "should", "about"}
    keywords = [kw for kw in keywords if kw not in stop_words]
    if not keywords:
        keywords = [w for w in question.lower().split() if len(w) > 2][:5]

    conditions = [DocumentChunk.content.ilike(f"%{kw}%") for kw in keywords[:10]]

    if len(conditions) >= 2:
        filter_expr = and_(*conditions)
    else:
        filter_expr = or_(*conditions) if conditions else True

    results = (
        db.query(DocumentChunk, Document.filename)
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(Document.processing_status == "completed")
        .filter(filter_expr)
        .limit(k)
        .all()
    )

    if not results and len(conditions) >= 2:
        results = (
            db.query(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .filter(Document.processing_status == "completed")
            .filter(or_(*conditions))
            .limit(k)
            .all()
        )

    return [
        {
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "filename": filename,
            "content": chunk.content,
            "score": 0.5,
        }
        for chunk, filename in results
    ]


# ---------------------------------------------------------------------------
# RAG pipeline
# ---------------------------------------------------------------------------

async def ask_question(question: str, db: Session, max_sources: int = 5) -> dict:
    """
    RAG pipeline:
    1. Query DO Knowledge Base retrieve API
    2. Fall back to SQL search if KB unavailable
    3. Build context and call Gradient AI for answer generation
    """
    hits = await kb_retrieve(question, num_results=max_sources)

    if not hits:
        logger.info("KB retrieve returned no results, using SQL fallback")
        hits = _sql_fallback_search(question, db, k=max_sources)

    if not hits:
        return {
            "answer": "I couldn't find relevant information in your documents. Make sure documents are uploaded and indexed in the Knowledge Base.",
            "sources": [],
            "model_used": GRADIENT_MODEL,
        }

    context_parts, sources = [], []
    for hit in hits:
        context_parts.append(f"[{hit['filename']}]: {hit['content']}")
        sources.append({
            "document_id": hit.get("document_id", ""),
            "filename": hit["filename"],
            "chunk_excerpt": hit["content"][:200],
            "relevance_score": round(float(hit.get("score", 0.0)), 4),
        })

    context = "\n\n".join(context_parts)
    user_prompt = RAG_USER_PROMPT.format(context=context, question=question)

    try:
        import asyncio

        def _sync_call():
            client = get_gradient_client()
            return client.chat.completions.create(
                model=GRADIENT_MODEL,
                messages=[
                    {"role": "system", "content": RAG_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )

        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_call),
            timeout=90.0,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Gradient AI call failed: {e}")
        answer = "I found relevant documents but the AI service is temporarily unavailable. Please try again."

    return {"answer": answer, "sources": sources, "model_used": GRADIENT_MODEL}


# ---------------------------------------------------------------------------
# Document processing (local chunking for SQL fallback)
# ---------------------------------------------------------------------------

async def process_document(
    document_id: str,
    file_content: bytes,
    filename: str,
    file_type: str,
    db: Session,
) -> None:
    """Process document: extract text + chunk for SQL fallback."""
    from models import Document, DocumentChunk

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        logger.error(f"Document {document_id} not found")
        return

    doc.processing_status = "processing"
    db.commit()

    try:
        text = extract_text(file_content, file_type)
        if not text.strip():
            raise ValueError("No text could be extracted from the document")

        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Document produced no chunks")

        for chunk_data in chunks:
            db_chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                token_count=chunk_data["token_count"],
                embedding_id=None,
            )
            db.add(db_chunk)

        doc.chunk_count = len(chunks)
        doc.processing_status = "completed"
        db.commit()

        kb_status = "KB active" if KB_ENDPOINT else "SQL fallback only"
        logger.info(f"Document {document_id} processed: {len(chunks)} chunks ({kb_status})")

    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {e}")
        doc.processing_status = "failed"
        doc.error_message = str(e)
        db.commit()


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

async def delete_document_embeddings(document_id: str) -> bool:
    """KB handles cleanup when files are removed from Spaces and reindexed."""
    return True
