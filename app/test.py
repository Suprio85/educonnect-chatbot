from graph_service import GraphService

graph_service = GraphService()

schema = graph_service.graph.schema

schema = schema.replace("{", "(")
schema = schema.replace("}", ")")

print("Schema:", schema)




