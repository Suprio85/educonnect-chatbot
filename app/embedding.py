from sentence_transformers import SentenceTransformer

class SimpleEmbeddings:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_query(self, text):
        return self.model.encode(text).tolist()

    def embed_documents(self, docs):
        return [self.model.encode(doc).tolist() for doc in docs]

