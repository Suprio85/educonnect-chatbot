"""FastAPI application exposing the Hybrid RAG chatbot.


 - /health endpoint
 - /chat endpoint (question -> answer)

Run:
  uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import time
import threading
from functools import lru_cache
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ragchain import create_hybrid_rag_chain
from graph_service import GraphService


app = FastAPI(title="EduConnect Chatbot API", version="0.1.0")


_init_lock = threading.Lock()
_graph_service: Optional[GraphService] = None
_hybrid_chain = None
_default_graph_only: bool = False  # Toggle for graph-only vs hybrid mode


def _initialize_if_needed() -> None:
	global _graph_service, _hybrid_chain
	if _hybrid_chain is not None:
		return
	with _init_lock:
		if _hybrid_chain is not None:
			return
		start = time.time()
		# Initialize GraphService 
		_graph_service = GraphService()
			
		# Ensure vector store exists for semantic retrieval
		if not hasattr(_graph_service, 'vector_store') or _graph_service.vector_store is None:
			print("[INIT] Creating vector store for semantic retrieval...")
			_graph_service.create_vector_store()
		
		_hybrid_chain = create_hybrid_rag_chain(_graph_service)
		elapsed = time.time() - start
		print(f"[INIT] Graph + Hybrid chain ready in {elapsed:.2f}s")


class ChatRequest(BaseModel):
	question: str
	graph_only: Optional[bool] = None  # If None, uses default setting
	stream: Optional[bool] = False  
	include_context: Optional[bool] = False


class ChatResponse(BaseModel):
	answer: str
	cached: bool
	elapsed_ms: float
	mode: str  # "graph_only" or "hybrid"
	graph_used: bool
	semantic_used: bool
	# Optional metadata
	graph_answer: Optional[str] = None
	semantic_chunks: Optional[int] = None



class _LRUCache:
	def __init__(self, max_size: int = 64):
		self.max_size = max_size
		self._data: Dict[str, Any] = {}
		self._order: list[str] = []
		self._lock = threading.Lock()

	def get(self, key: str):
		with self._lock:
			if key in self._data:
				self._order.remove(key)
				self._order.append(key)
				return self._data[key]
			return None

	def set(self, key: str, value: Any):
		with self._lock:
			if key in self._data:
				self._order.remove(key)
			elif len(self._order) >= self.max_size:
				oldest = self._order.pop(0)
				self._data.pop(oldest, None)
			self._data[key] = value
			self._order.append(key)


_cache = _LRUCache(max_size=128)


@app.on_event("startup")
def startup_event():
	_initialize_if_needed()


@app.get("/health")
def health():
	try:
		_initialize_if_needed()
		_graph_service.graph.query("RETURN 1 AS ok")
		return {"status": "ok"}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
	if not req.question or not req.question.strip():
		raise HTTPException(status_code=400, detail="Question must not be empty")

	_initialize_if_needed()

	# Determine mode: use request-specific setting or global default
	use_graph_only = _default_graph_only if req.graph_only is None else req.graph_only
	cache_key = f"{req.question}::{use_graph_only}"
	
	cached_payload = _cache.get(cache_key)
	if cached_payload is not None:
		return ChatResponse(
			answer=cached_payload["answer"],
			cached=True,
			elapsed_ms=0.0,
			mode=cached_payload.get("mode", "hybrid"),
			graph_used=cached_payload.get("graph_used", True),
			semantic_used=cached_payload.get("semantic_used", True),
			graph_answer=cached_payload.get("graph_answer") if req.include_context else None,
			semantic_chunks=cached_payload.get("semantic_chunks") if req.include_context else None,
		)
	
	start = time.time()
	try:
		invoke_params = {"question": req.question}
		if use_graph_only:
			invoke_params["graph_only"] = True
		result = _hybrid_chain.invoke(invoke_params)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Inference failed: {e}")
	elapsed_ms = (time.time() - start) * 1000

	semantic_docs = result.get("semantic_documents") or []
	mode = result.get("mode", "hybrid")
	
	payload = {
		"answer": result["answer"],
		"mode": mode,
		"graph_answer": result.get("graph_answer"),
		"semantic_chunks": len(semantic_docs),
		"graph_used": bool(result.get("graph_answer")),
		"semantic_used": len(semantic_docs) > 0,
	}
	_cache.set(cache_key, payload)

	return ChatResponse(
		answer=payload["answer"],
		cached=False,
		elapsed_ms=elapsed_ms,
		mode=payload["mode"],
		graph_used=payload["graph_used"],
		semantic_used=payload["semantic_used"],
		graph_answer=payload["graph_answer"] if req.include_context else None,
		semantic_chunks=payload["semantic_chunks"] if req.include_context else None,
	)


@app.post("/clear-cache")
def clear_cache():
	global _cache
	_cache = _LRUCache(max_size=128)
	return {"cleared": True}


@app.get("/mode")
def get_mode():
	"""Get current default mode setting"""
	return {
		"default_graph_only": _default_graph_only,
		"mode": "graph_only" if _default_graph_only else "hybrid"
	}


class ModeRequest(BaseModel):
	graph_only: bool


@app.post("/mode")
def set_mode(req: ModeRequest):
	global _default_graph_only
	_default_graph_only = req.graph_only
	return {
		"updated": True,
		"default_graph_only": _default_graph_only,
		"mode": "graph_only" if _default_graph_only else "hybrid"
	}


if __name__ == "__main__":
	import uvicorn
	uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
