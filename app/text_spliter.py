from langchain_text_splitters import RecursiveCharacterTextSplitter
from convert_to_docs import convert_to_docs
from config import DATA_LOCATION


def text_splitter(chunk_size=400, chunk_overlap=40):

    docs = convert_to_docs(DATA_LOCATION)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    texts = text_splitter.split_documents(docs)
    return texts

