#!/usr/bin/env python3
"""
Quick test script for graph_only vs hybrid modes
"""

from app.ragchain import create_hybrid_rag_chain
from app.graph_service import GraphService
import time

def test_modes():
    print("Initializing graph service...")
    graph_service = GraphService()
    hybrid_chain = create_hybrid_rag_chain(graph_service)
    
    test_question = "What are the top universities?"
    
    print(f"\nTesting question: '{test_question}'\n")
    
    # Test hybrid mode
    print("=" * 50)
    print("HYBRID MODE (graph + semantic)")
    print("=" * 50)
    start = time.time()
    result_hybrid = hybrid_chain.invoke({"question": test_question, "graph_only": False})
    hybrid_time = time.time() - start
    
    print(f"Time taken: {hybrid_time:.2f}s")
    print(f"Mode: {result_hybrid.get('mode', 'N/A')}")
    print(f"Semantic docs count: {len(result_hybrid.get('semantic_documents', []))}")
    print(f"Answer: {result_hybrid['answer'][:200]}...")
    
    # Test graph-only mode
    print("\n" + "=" * 50)
    print("GRAPH-ONLY MODE (faster)")
    print("=" * 50)
    start = time.time()
    result_graph = hybrid_chain.invoke({"question": test_question, "graph_only": True})
    graph_time = time.time() - start
    
    print(f"Time taken: {graph_time:.2f}s")
    print(f"Mode: {result_graph.get('mode', 'N/A')}")
    print(f"Semantic docs count: {len(result_graph.get('semantic_documents', []))}")
    print(f"Answer: {result_graph['answer'][:200]}...")
    
    print(f"\nSpeed improvement: {((hybrid_time - graph_time) / hybrid_time * 100):.1f}% faster")

if __name__ == "__main__":
    test_modes()