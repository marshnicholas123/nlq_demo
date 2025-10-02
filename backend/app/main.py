from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import text2sql

app = FastAPI(
    title="Nuclear Power Text2SQL API",
    description="Demo application for Text2SQL variants",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(text2sql.router, prefix="/api/text2sql", tags=["text2sql"])

@app.get("/")
async def root():
    return {
        "message": "Nuclear Power Text2SQL API",
        "endpoints": [
            "/api/text2sql/simple",
            "/api/text2sql/advanced",
            "/api/text2sql/chat",
            "/api/text2sql/agentic"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}