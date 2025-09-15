# EduConnect Chatbot - Setup Guide

This guide provides step-by-step instructions to set up and run the EduConnect Chatbot in your local or cloud environment.

---

## 1. Prerequisites

- **Python 3.10+** (Recommended: 3.11 or 3.13)
- **Neo4j Database** (Cloud: Neo4j Aura or Local)
- **Google Gemini API Key** (for LLM-powered features)
- **Internet connection** (for package installation and LLM access)

---

## 2. Clone the Repository

```bash
git clone <your-repo-url>
cd educonnect-chatbot
```

---

## 3. Python Environment Setup

It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

## 4. Install Dependencies

All required packages are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 5. Environment Variables

Create a `.env` file in the root directory with the following variables:

```
NEO4J_URI=bolt://<your-neo4j-host>:7687
NEO4J_USER=<your-username>
NEO4J_PASSWORD=<your-password>
GEMINI_API_KEY=<your-google-gemini-api-key>
GEMINI_MODEL_NAME=gemini-pro
GEMINI_MAX_TOKENS=2048
GEMINI_TEMPERATURE=0.2
DATA_LOCATION=../data
```

- Adjust `DATA_LOCATION` if your data folder is elsewhere.
- Use a read-only Neo4j user for production.

---

## 6. Prepare Data

- Place your `universities.json` file in the `data/` directory.
- The file should contain an array of university objects with properties as described in the architecture documentation.

---

## Now goto app directory

```
 cd app
```

## 7. Initialize the Graph and Vector Store

The first run should build the graph and vector index:

```python
# In Python REPL or a script:
from graph_service import GraphService
service = GraphService(build_graph=True)
# This will populate the graph and create the vector store.
```

Alternatively, you can add a CLI or script to automate this step.

---

## 8. Run the FastAPI Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- The API will be available at `http://localhost:8000`.
- Use `/docs` for interactive Swagger UI.

---

## 9. API Usage

### Chat Endpoint

```http
POST /chat
{
  "question": "What are the top universities for computer science?",
  "graph_only": false,  # Optional: true for fast mode
  "include_context": true  # Optional: include raw context in response
}
```

### Mode Control

```http
GET /mode
POST /mode { "graph_only": true }
```

### Health and Cache

```http
GET /health
POST /clear-cache
```

---

## 10. Troubleshooting

- **Neo4j connection errors:** Check your URI, credentials, and network/firewall settings.
- **Gemini API errors:** Ensure your API key is valid and has sufficient quota.
- **Data ingestion issues:** Validate your `universities.json` format and required fields.
- **Vector store not found:** Make sure you ran the graph initialization step.

---

## 11. Customization

- To change the data model, edit `app/graph_service.py` and update the ingestion logic.
- To adjust LLM prompt behavior, modify `app/ragchain.py`.
- For advanced deployment (Docker, cloud), adapt the above steps as needed.

---

## 12. Support

For questions or issues, please open an issue in the repository or contact the maintainer.
