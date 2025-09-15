from config import Neo4jConfig, GeminiConfig, DATA_LOCATION
from langchain_neo4j import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from convert_to_docs import convert_to_docs
import json
from embedding import SimpleEmbeddings

class GraphService:
    def __init__(self, build_graph=False):
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

        if build_graph:
            self._populate_graph()
            # self.populate_with_llm()

            print("Graph has been initialized and documents have been added.")
            print("Graph details and visualization can be found in the Neo4j dashboard.")
        self.create_vector_store()

    def _clear_graph(self):
        self.graph.query("MATCH (n) DETACH DELETE n")


    def _populate_graph(self):
     with open(f"{DATA_LOCATION}/universities.json", "r") as file:
        universities = json.load(file)

        if isinstance(universities, dict):
            universities = [universities]

        for uni in universities:
            name = uni["university_name"]
            location = uni.get("location", "Unknown")
            rank = uni.get("rank", 0)
            tuition_fee = uni.get("tuition_fee", 0)
            acceptance_rate = uni.get("acceptance_rate", "Unknown")
            website = uni.get("website", "")
            
            programs = uni.get("programs", [])
            requirements = uni.get("requirements", {})
            
            print(f"Adding university: {name}")
            
            # Create University node with all properties
            university_cypher = """
            MERGE (u:University {name: $name})
            SET u.location = $location,
                u.rank = $rank,
                u.tuition_fee = $tuition_fee,
                u.acceptance_rate = $acceptance_rate,
                u.website = $website
            """
            
            self.graph.query(
                university_cypher,
                params={
                    "name": name,
                    "location": location,
                    "rank": rank,
                    "tuition_fee": tuition_fee,
                    "acceptance_rate": acceptance_rate,
                    "website": website
                }
            )
            
            # Create Location node and relationship
            if location != "Unknown":
                # Extract city and state/country from location
                location_parts = location.split(", ")
                city = location_parts[0] if len(location_parts) > 0 else location
                state = location_parts[1] if len(location_parts) > 1 else ""
                country = location_parts[2] if len(location_parts) > 2 else ""
                
                location_cypher = """
                MATCH (u:University {name: $name})
                MERGE (l:Location {name: $location})
                SET l.city = $city,
                    l.state = $state,
                    l.country = $country
                MERGE (u)-[:LOCATED_IN]->(l)
                """
                
                self.graph.query(
                    location_cypher,
                    params={
                        "name": name,
                        "location": location,
                        "city": city,
                        "state": state,
                        "country": country
                    }
                )
            
            # Create Program nodes and relationships
            for program in programs:
                program_cypher = """
                MATCH (u:University {name: $name})
                MERGE (p:Program {name: $program})
                MERGE (u)-[:OFFERS]->(p)
                """
                
                self.graph.query(
                    program_cypher,
                    params={
                        "name": name,
                        "program": program
                    }
                )
            
            # Create Requirements node and relationships
            if requirements:
                min_gpa = requirements.get("minimum_gpa", 0.0)
                required_tests = requirements.get("required_tests", [])
                scholarship_options = requirements.get("scholarship_options", [])
                
                requirements_cypher = """
                MATCH (u:University {name: $name})
                MERGE (r:Requirements {university: $name})
                SET r.minimum_gpa = $min_gpa
                MERGE (u)-[:HAS_REQUIREMENTS]->(r)
                """
                
                self.graph.query(
                    requirements_cypher,
                    params={
                        "name": name,
                        "min_gpa": min_gpa
                    }
                )
                
              
                for test in required_tests:
                    test_cypher = """
                    MATCH (u:University {name: $name})
                    MERGE (t:Test {name: $test})
                    MERGE (u)-[:REQUIRES_TEST]->(t)
                    """
    
                    self.graph.query(
                    test_cypher,
                    params={
                    "name": name,
                    "test": test
                }
                )

                
                
                for scholarship in scholarship_options:
                    scholarship_cypher = """
                    MATCH (u:University {name: $name})
                    MERGE (s:Scholarship {type: $scholarship})
                    MERGE (u)-[:OFFERS_SCHOLARSHIP]->(s)
                    """
                    
                    self.graph.query(
                        scholarship_cypher,
                        params={
                            "name": name,
                            "scholarship": scholarship
                        }
                    )
            
            
            similar_programs_cypher = """
            MATCH (u1:University {name: $name})-[:OFFERS]->(p:Program)
            MATCH (u2:University)-[:OFFERS]->(p)
            WHERE u1 <> u2
            MERGE (u1)-[:SHARES_PROGRAM_WITH]->(u2)
            """
            
            self.graph.query(
                similar_programs_cypher,
                params={"name": name}
            )
        
        
        self._create_additional_relationships()
    
    def _create_additional_relationships(self):
        """Create additional relationships to enrich the graph"""
        
        
        print("Creating ranking tiers...")
        
        self.graph.query("""
            MATCH (u:University)
            WHERE u.rank <= 10
            MERGE (t:Tier {name: "Top 10"})
            MERGE (u)-[:BELONGS_TO_TIER]->(t)
        """)
        
      
        self.graph.query("""
            MATCH (u:University)
            WHERE u.rank > 10 AND u.rank <= 25
            MERGE (t:Tier {name: "Top 25"})
            MERGE (u)-[:BELONGS_TO_TIER]->(t)
        """)
        
        
        self.graph.query("""
            MATCH (u:University)
            WHERE u.rank > 25 AND u.rank <= 50
            MERGE (t:Tier {name: "Top 50"})
            MERGE (u)-[:BELONGS_TO_TIER]->(t)
        """)
        
        
        self.graph.query("""
            MATCH (u:University)
            WHERE u.rank > 50
            MERGE (t:Tier {name: "Other"})
            MERGE (u)-[:BELONGS_TO_TIER]->(t)
        """)
        
        print("Creating fee ranges...")
        
        
        self.graph.query("""
            MATCH (u:University)
            WHERE u.tuition_fee >= 50000
            MERGE (f:FeeRange {range: "High (50K+)"})
            MERGE (u)-[:HAS_FEE_RANGE]->(f)
        """)
        
        
        self.graph.query("""
            MATCH (u:University)
            WHERE u.tuition_fee >= 30000 AND u.tuition_fee < 50000
            MERGE (f:FeeRange {range: "Medium (30K-50K)"})
            MERGE (u)-[:HAS_FEE_RANGE]->(f)
        """)
        
        
        self.graph.query("""
            MATCH (u:University)
            WHERE u.tuition_fee < 30000
            MERGE (f:FeeRange {range: "Low (<30K)"})
            MERGE (u)-[:HAS_FEE_RANGE]->(f)
        """)
        
        print("Creating location relationships...")
        
       
        self.graph.query("""
            MATCH (l1:Location), (l2:Location)
            WHERE l1.state = l2.state AND l1 <> l2 AND l1.state <> ""
            MERGE (l1)-[:SAME_STATE]->(l2)
        """)
        
        print("Creating acceptance rate categories...")
        
        
        self.graph.query("""
            MATCH (u:University)
            WHERE toFloat(replace(u.acceptance_rate, '%', '')) < 10
            MERGE (a:AcceptanceCategory {category: "Highly Selective (<10%)"})
            MERGE (u)-[:HAS_ACCEPTANCE_RATE]->(a)
        """)
        
        self.graph.query("""
            MATCH (u:University)
            WHERE toFloat(replace(u.acceptance_rate, '%', '')) >= 10 AND toFloat(replace(u.acceptance_rate, '%', '')) < 30
            MERGE (a:AcceptanceCategory {category: "Selective (10-30%)"})
            MERGE (u)-[:HAS_ACCEPTANCE_RATE]->(a)
        """)
        
        self.graph.query("""
            MATCH (u:University)
            WHERE toFloat(replace(u.acceptance_rate, '%', '')) >= 30
            MERGE (a:AcceptanceCategory {category: "Moderately Selective (30%+)"})
            MERGE (u)-[:HAS_ACCEPTANCE_RATE]->(a)
        """)
        
        print("All additional relationships created successfully!")
 
    def populate_with_llm(self):
        prompt_template = PromptTemplate(
           template="Keep in mind that the context is about educational institutions and related topics. Users wil ask about the details about various universities, courses, admission processes, and other related information. Use the context to provide accurate and relevant answers. so keep nodes and relationship accordingly",
        )

        
        docs = convert_to_docs(DATA_LOCATION)
        transformer = LLMGraphTransformer(
                llm=self.llm,
                node_properties=False,
                relationship_properties=False,
                prompt=prompt_template
            )

        graph_doc = transformer.convert_to_graph_documents(docs)
        self.graph.add_graph_documents(graph_doc)

    def create_vector_store(self):
        try:
            self.vector_store = Neo4jVector.from_existing_graph(
            embedding=self.embeddings,
            url=Neo4jConfig.URI,
            username=Neo4jConfig.USER,
            password=Neo4jConfig.PASSWORD,
            index_name="university_index",
            node_label="University",
            text_node_properties=["name", "location", "website", "rank", "tuition_fee", "acceptance_rate"],  # Fixed: 'rank' not 'Rank'
            embedding_node_property="embedding",
            search_type='hybrid' 
            )
            print("Vector store created successfully!")
        except Exception as e:
            print(f"Warning: Could not create vector store: {e}")
            print("Semantic retrieval will not be available")
            self.vector_store = None




        



       

       

       





