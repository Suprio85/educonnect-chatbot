from graph_service import GraphService
from ragchain import create_hybrid_rag_chain


def print_divider(title: str):
	print("\n" + "=" * 90)
	print(title)
	print("=" * 90)


def run_query(chain, question: str):
	try:
		result = chain.invoke({"question": question})
	except Exception as e:
		print(f"❌ Error for question '{question}': {e}")
		return

	print_divider(f"QUESTION: {question}")
	print("\nFINAL ANSWER:\n" + result["answer"])
	print("\n— Structured Graph Answer Snippet —\n" + (result.get("graph_answer") or "(none)"))

	sem_docs = result.get("semantic_documents") or []
	if sem_docs:
		print("\n— Top Semantic Chunks (truncated) —")
		for i, d in enumerate(sem_docs[:3]):
			snippet = d.page_content[:220].replace("\n", " ")
			print(f"[{i+1}] {snippet}...")
	else:
		print("\n(No semantic documents retrieved)")

	steps = result.get("cypher_steps")
	if steps:
		print("\n— Cypher Steps (raw) —")
		print(steps if isinstance(steps, str) else str(steps)[:800])


def main():
	print_divider("Initializing Graph Service")
	graph_service = GraphService()

	print_divider("Creating Hybrid RAG Chain")
	hybrid_chain = create_hybrid_rag_chain(graph_service)

	evaluation_queries = [
		"List top ranked universities offering Computer Science.",
		"Which universities have low tuition but good rankings?",
		"What tests are required for MIT and Stanford?",
		"Compare acceptance rates of Berkeley and Carnegie Mellon.",
		"Suggest scholarships offered by Georgia Tech.",
		"What programs are common between MIT and Stanford?",
	]

	for q in evaluation_queries:
		run_query(hybrid_chain, q)

	print_divider("Done")


if __name__ == "__main__":
	main()


