from config import Neo4jConfig, GeminiConfig, DATA_LOCATION
from langchain_neo4j import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from  convert_to_docs import convert_to_docs


from embedding import SimpleEmbeddings

class GraphService():
    def __init__(self):
        self.graph = Neo4jGraph(
            url=Neo4jConfig.URI,
            username=Neo4jConfig.USER,
            password=Neo4jConfig.PASSWORD
        )
        geminiConfig = GeminiConfig()

        self.embeddings = SimpleEmbeddings()

        self.llm = ChatGoogleGenerativeAI(
            model=geminiConfig.MODEL_NAME,
            google_api_key=geminiConfig.API_KEY,
            max_tokens=geminiConfig.MAX_TOKENS,
            temperature=geminiConfig.TEMPERATURE
        )

        prompt_template = PromptTemplate(
           template="Keep in mind that the context is about educational institutions and related topics. Users wil ask about the details about various universities, courses, admission processes, and other related information. Use the context to provide accurate and relevant answers. so keep nodes and relationship accordingly",
        )

        # docs = text_splitter()
        docs = convert_to_docs(DATA_LOCATION)
        transformer = LLMGraphTransformer(
        llm = self.llm,
        node_properties=False,
        relationship_properties=False,
        prompt= prompt_template
        )

        graph_doc = transformer.convert_to_graph_documents(docs)
        self.graph.add_graph_documents(graph_doc)

        print("Graph has been initialized and documents have been added.")
        print("Graph details and visualization can be found in the Neo4j dashboard.")

        



       

       

       





