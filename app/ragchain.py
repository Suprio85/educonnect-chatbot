from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from config import Neo4jConfig, GeminiConfig, DATA_LOCATION
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from typing import Any, Dict, List
import json


class HybridRAGChain:
    """Hybrid Retrieval-Augmented Generation chain that:
    1. Generates Cypher and answers via the Neo4j structured graph (GraphCypherQAChain)
    2. Performs semantic retrieval from the Neo4j vector index
    3. Synthesizes a final answer using both sources

    Usage:
        hybrid = create_hybrid_rag_chain(graph_service)
        result = hybrid.invoke({"question": "What universities offer Computer Science with low tuition?"})
        print(result["answer"])
    """

    def __init__(self, graph_chain, retriever, llm):
        self.graph_chain = graph_chain
        self.retriever = retriever
        self.llm = llm

        self.combine_prompt = ChatPromptTemplate.from_template(
            (
                "You are EduConnect, an educational guidance assistant.\n"
                "User question: {question}\n\n"
                "Structured graph answer (may be partial):\n{graph_answer}\n\n"
                "Relevant semantic context chunks (unstructured):\n{semantic_context}\n\n"
                "Cypher / reasoning steps (for transparency):\n{cypher_steps}\n\n"
                "Instructions:\n"
                "1. Provide a concise, accurate, student-friendly answer.\n"
                "2. Combine structured facts (graph) with supplemental context (semantic). if one is more relevant, prioritize it. if one don't know answer then prioritize the other answer with your knowledge\n"
                "3. If there are ranking / tuition / GPA details, include them succinctly.\n"
                "4. Suggest 1–2 follow-up guidance tips when helpful.\n"
                "5. If information is missing from both sources(structured graph and semantic context), state that briefly instead of hallucinating.\n\n"
                "Final Answer:"
            )
        )

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        question = inputs.get("question") or inputs.get("query")
        if not question:
            raise ValueError("'question' key is required in inputs")

        # 1. Structured graph QA (returns cypher + answer)
        graph_result = self.graph_chain.invoke({"query": question})
        graph_answer = graph_result.get("result", "")
        cypher_steps = graph_result.get("intermediate_steps", [])

        # 2. Semantic retrieval
        semantic_docs = []
        if self.retriever is not None:
            try:
                semantic_docs = self.retriever.get_relevant_documents(question)
            except Exception as e:
                semantic_docs = []
                graph_answer += f"\n(Note: semantic retrieval failed: {e})"

        semantic_context = "\n---\n".join(d.page_content for d in semantic_docs[:6]) if semantic_docs else "(No semantic context retrieved)"

        # 3. final answer
        messages = self.combine_prompt.format_messages(
            question=question,
            graph_answer=graph_answer,
            semantic_context=semantic_context,
            cypher_steps=json.dumps(cypher_steps, indent=2) if cypher_steps else "(No cypher details)"
        )
        final_response = self.llm.invoke(messages)
        final_text = getattr(final_response, "content", str(final_response))

        return {
            "answer": final_text.strip(),
            "graph_answer": graph_answer,
            "semantic_documents": semantic_docs,
            "cypher_steps": cypher_steps,
            "raw_graph_result": graph_result,
        }

def create_hybrid_rag_chain(graph_service):
    """
    Create a hybrid RAG chain using:
    1. Neo4j structured graph (GraphCypherQAChain)
    2. Neo4j vector embeddings (semantic search)
    """

    cypher_prompt = PromptTemplate(
        template="""
        You are an expert at converting natural language questions about universities into Cypher queries.
        The graph schema includes these node types and relationships:

        NODES:
        - University: name, location, rank, tuition_fee, acceptance_rate, website
        - Location: name, city, state, country
        - Program: name
        - Requirements: university_name, minimum_gpa
        - Test: name (SAT, TOEFL, etc.)
        - Scholarship: type (Need-based, Merit-based, Athletic, etc.)
        - Tier: name (Top 10, Top 25, Top 50, Other)
        - FeeRange: range (High, Medium, Low)
        - AcceptanceCategory: category (Highly Selective, Selective, Moderately Selective)

        RELATIONSHIPS:
        - (University)-[:LOCATED_IN]->(Location)
        - (University)-[:OFFERS]->(Program)
        - (University)-[:HAS_REQUIREMENTS]->(Requirements)
        - (University)-[:REQUIRES_TEST]->(Test)
        - (University)-[:OFFERS_SCHOLARSHIP]->(Scholarship)
        - (University)-[:BELONGS_TO_TIER]->(Tier)
        - (University)-[:HAS_FEE_RANGE]->(FeeRange)
        - (University)-[:HAS_ACCEPTANCE_RATE]->(AcceptanceCategory)
        - (Requirements)-[:INCLUDES_TEST]->(Test)

        IMPORTANT GUIDELINES:
        1. Always use proper Cypher syntax
        2. Use MATCH for finding existing nodes
        3. Use WHERE clauses for filtering
        4. Return relevant properties
        5. Use LIMIT when appropriate
        6. Handle case-insensitive matching with toLower()
        7. For acceptance rates, remember they're stored as strings with % (e.g., "7%")
        8. Combine multiple conditions with AND / OR as needed
        9. When Opportunities ie Scholarships are mentioned, include them in the query
        10. if no query can be generated, Answer based your own knowledge base if you are sure. otherwise, say "I don't know"

        Examples:
        - "universities in California" -> MATCH (u:University)-[:LOCATED_IN]->(l:Location) WHERE toLower(l.state) CONTAINS 'california'
        - "top 10 universities" -> MATCH (u:University)-[:BELONGS_TO_TIER]->(t:Tier {{"name": "Top 10"}})
        - "universities offering computer science" -> MATCH (u:University)-[:OFFERS]->(p:Program) WHERE toLower(p.name) CONTAINS 'computer science'
        - "Test required in a specific university" -> MATCH (u:University {{"name": "MIT"}})-[:REQUIRES_TEST]->(t:Test) RETURN t.name

        Question: {question}
        Generate only the Cypher query, no explanations
        Cypher:""",
        input_variables=["question"]
    )
   


    graph_chain = GraphCypherQAChain.from_llm(
        llm=graph_service.llm,
        graph=graph_service.graph,
        verbose=False,
        return_intermediate_steps=True,
        validate_cypher=True,
        top_k=10,
        cypher_prompt=cypher_prompt,
        allow_dangerous_requests=True
    )

    retriever = None
    if getattr(graph_service, "vector_store", None) is not None:
        try:
            retriever = graph_service.vector_store.as_retriever(
                search_type="hybrid", 
                search_kwargs={"k": 6}
            )
        except Exception:
            # Fallback to similarity if hybrid not supported
            retriever = graph_service.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 6}
            )

    return HybridRAGChain(
        graph_chain=graph_chain,
        retriever=retriever,
        llm=graph_service.llm
    )

