import os
import json
from typing import List, Dict, Union
from PyPDF2 import PdfReader
from langchain_core.documents import Document
from config import DATA_LOCATION

def convert_to_docs(folder_path: str) -> List[Document]:
    """
    Convert files in a folder to LangChain Documents.
    Traverses the folder and processes JSON, PDF, and TXT files.
    """
    documents = []  
    
    if os.path.isfile(folder_path):
       
        file_paths = [folder_path]
    elif os.path.isdir(folder_path):
        
        file_paths = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_paths.append(os.path.join(root, file))
    else:
        raise ValueError(f"Path does not exist: {folder_path}")
    
  
    for file_path in file_paths:
        try:
            file_extension = os.path.splitext(file_path)[-1].lower()
            docs = []

            if file_extension == ".json":
                docs = _convert_json_to_docs(file_path)
            elif file_extension == ".pdf":
                docs = _convert_pdf_to_docs(file_path)
            elif file_extension == ".txt":
                docs = _convert_text_to_docs(file_path)
            else:
                print(f"Skipping unsupported file type: {file_path}")
                continue

          
            for doc in docs:
                
                if isinstance(doc, dict):
                 
                    page_content = json.dumps(doc)
                    metadata = {
                        "file_type": file_extension,
                        "website": doc.get("website", ""),
                        "location": doc.get("location", ""),
                        "name": doc.get("university_name", doc.get("name", ""))
                    }
                elif isinstance(doc, str):
                    page_content = doc
                    metadata = {            
                        "file_type": file_extension
                    }
                else:
                    page_content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
                    metadata = doc.metadata if hasattr(doc, 'metadata') else {"source": file_path}
                
                documents.append(Document(
                    page_content=page_content,
                    metadata=metadata
                ))
                
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            continue
    
    return documents

    
   


def _convert_json_to_docs(file_path: str) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Converts a JSON file into structured docs.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        List[Dict[str, Union[str, List[str]]]]: A list of structured docs.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]  # Ensure it's a list of dictionaries

    docs = []
    for item in data:
        doc = {
            "university_name": item.get("university_name"),
            "location": item.get("location"),
            "rank": item.get("rank"),
            "tuition_fee": item.get("tuition_fee"),
            "acceptance_rate": item.get("acceptance_rate"),
            "requirements": item.get("requirements"),
            "programs": item.get("programs"),
            "website": item.get("website"),
        }
        docs.append(doc)

    return docs


def _convert_pdf_to_docs(file_path: str) :
    """
    Converts a PDF file into structured docs.

    Args:
        file_path (str): Path to the PDF file.

    Returns:
        Document
    """
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    # Split text into lines and process (assuming a structured format in the PDF)
    lines = text.split("\n")
    docs = []
    current_doc = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        current_doc += line

    return [current_doc]


def _convert_text_to_docs(file_path: str) :
    """
    Converts a text file into structured docs.

    Args:
        file_path (str): Path to the text file.

    Returns:
        Document
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_doc=""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        current_doc = current_doc + line

        

    return [current_doc]

