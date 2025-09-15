# EduConnect Chatbot - Setup Guide

This guide provides step-by-step instructions to set up and run the EduConnect Chatbot in your local or cloud environment.

---

## 1. Prerequisites

- **Python 3.10+** (Recommended: 3.11 or 3.13)
- **Neo4j Aura Cloud Database** (Free tier available at https://neo4j.com/aura/)
- **Google Gemini API Key** (for LLM-powered features)
- **Internet connection** (for package installation and LLM access)

---

## 2. Setup Neo4j Aura Database

1. **Create a free Neo4j Aura account** at https://neo4j.com/aura/
2. **Create a new database instance** (select the free tier)
3. **Download the connection details** (.txt file) provided by Aura
4. **Note down your database URI, username, and password** - you'll need these for environment variables

---

## 3. Clone the Repository

```bash
git clone <repo-url>
cd educonnect-chatbot
```

---

## 4. Python Environment Setup

It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

## 5. Install Dependencies

All required packages are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 6. Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Neo4j Aura Database (use the connection details from your Aura instance)
NEO4J_URI=neo4j+s://your-instance-id.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-generated-password

# Google Gemini API
GEMINI_API_KEY=your-google-gemini-api-key
GEMINI_MODEL_NAME=gemini-pro
GEMINI_MAX_TOKENS=2048
GEMINI_TEMPERATURE=0.2

# Data location
DATA_LOCATION=../data
```

**Important Notes:**
- Use the **exact connection details** provided by Neo4j Aura (URI format will be `neo4j+s://...`)
- Get your **Gemini API key** from Google AI Studio: https://makersuite.google.com/app/apikey
- Adjust `DATA_LOCATION` if your data folder is elsewhere

---

## 7. Prepare Data

- Place your `universities.json` file in the `data/` directory.
- The file should contain an array of university objects with properties as described in the architecture documentation.

---

## Now goto app directory

```
 cd app
```

## 8. Initialize the Graph and Vector Store

The first run should build the graph and vector index:

```python
# In Python REPL or a script:
from graph_service import GraphService
service = GraphService(build_graph=True)
# This will populate the graph and create the vector store.
```

Alternatively, you can add a CLI or script to automate this step.

---

## 9. Run the FastAPI Server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- The API will be available at `http://localhost:8000`.
- Use `/docs` for interactive Swagger UI.

---

## 10. API Usage

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

## 11. Troubleshooting

- **Neo4j connection errors:** Check your Aura connection details, ensure you're using the correct URI format (`neo4j+s://...`)
- **Gemini API errors:** Ensure your API key is valid and has sufficient quota
- **Data ingestion issues:** Validate your `universities.json` format and required fields
- **Vector store not found:** Make sure you ran the graph initialization step

---

## 12. Customization

- To change the data model, edit `app/graph_service.py` and update the ingestion logic.
- To adjust LLM prompt behavior, modify `app/ragchain.py`.
- For advanced deployment (Docker, cloud), adapt the above steps as needed.

---

## 13. Docker Setup

### Prerequisites for Docker

- **Docker** installed on your system
- **Docker Compose** (usually included with Docker Desktop)

### Build and Run with Docker

1. **Ensure your `.env` file is in the root directory** with all required environment variables.

2. **Build and start the container:**

```bash
docker-compose up --build
```

3. **For production deployment (detached mode):**

```bash
docker-compose up -d --build
```

4. **View logs:**

```bash
docker-compose logs -f educonnect-api
```

5. **Stop the container:**

```bash
docker-compose down
```

### Docker Environment Notes

- The Docker setup includes automatic restarts and health checks
- Application runs as a non-root user for security
- Data and app directories are mounted as volumes for development
- For production, consider removing the `--reload` flag and volume mounts

### Render Deployment with Docker

For deploying to Render.com:

1. **Create a `render.yaml` file:**

```yaml
services:
  - type: web
    name: educonnect-chatbot
    env: docker
    dockerfilePath: ./Dockerfile
    region: oregon
    plan: starter
    envVars:
      - key: NEO4J_URI
        value: neo4j+s://your-aura-instance.databases.neo4j.io
      - key: NEO4J_USER
        value: neo4j
      - key: NEO4J_PASSWORD
        value: your-aura-password
      - key: GEMINI_API_KEY
        value: your-gemini-api-key
```

2. **Connect your GitHub repository to Render**
3. **Set environment variables in Render dashboard using your Neo4j Aura connection details**
4. **Deploy automatically on git push**

---

## 14. Support

For questions or issues, please open an issue in the repository or contact the maintainer.
