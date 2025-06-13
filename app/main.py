from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os
import pandas as pd
import json

app = FastAPI()

# Set up static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

class SearchQuery(BaseModel):
    query: str

class PaperInfo(BaseModel):
    id: str
    title: str 
    authors: List[str]
    abstract: str
    pdf_url: str
    md_path: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/classic", response_class=HTMLResponse)
async def classic_papers(request: Request):
    return templates.TemplateResponse("classic.html", {"request": request})

@app.get("/latest", response_class=HTMLResponse)
async def latest_papers(request: Request):
    return templates.TemplateResponse("latest.html", {"request": request})

# Semantic Scholar Endpoints
@app.post("/api/semantic/search")
async def search_semantic(query: SearchQuery):
    """Search Semantic Scholar papers"""
    import pandas as pd
    try:
        df = pd.DataFrame([json.loads(i) for i in open("data/semantic/meta_paper.jsonl", 'r').readlines()])

        df = df[df['pdf_url'].apply(lambda x: type(x) == type(''))]
        if query.query:
            # Simple keyword search in title and abstract
            mask = (df['title'].str.contains(query.query, case=False)) | \
                   (df['abstract'].str.contains(query.query, case=False))
            results = df[mask].to_dict('records')
        else:
            results = df.to_dict('records')
            
        # Convert to PaperInfo format
        papers = []
        for row in results:
            papers.append({
                "id": row["paper_id"],
                "title": row["title"],
                "authors": row["authors"].split(";"),
                "abstract": row["abstract"],
                "pdf_url": row["pdf_url"],
                "md_path": row["markdown_path"]
            })
        return {"results": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/semantic/crawl")
async def crawl_semantic(query: SearchQuery):
    """Crawl Semantic Scholar papers"""
    # In a real implementation, this would trigger a crawl
    # For now just return success since we're using pre-crawled data
    return {"status": "success"}

@app.post("/api/semantic/read")
async def read_semantic(papers: List[PaperInfo]):
    """Request LLM to read Semantic papers"""
    # In a real implementation, this would trigger LLM processing
    # For now just return success since we're using pre-generated summaries
    print('heelo')
    return {"status": "success"}

# ArXiv Endpoints 
@app.post("/api/arxiv/search")
async def search_arxiv(query: SearchQuery):
    """Search ArXiv papers"""
    import pandas as pd
    try:
        df = pd.read_csv("data/arxiv/meta_paper.csv")
        df = df[df['pdf_url'].apply(lambda x: type(x) == type(''))]
        if query.query:
            # Simple keyword search in title and abstract
            mask = (df['title'].str.contains(query.query, case=False)) | \
                   (df['abstract'].str.contains(query.query, case=False))
            results = df[mask].to_dict('records')
        else:
            results = df.to_dict('records')
            
        # Convert to PaperInfo format
        papers = []
        for row in results:
            papers.append({
                "id": row["paper_id"],
                "title": row["title"],
                "authors": row["authors"].split(";"),
                "abstract": row["abstract"],
                "pdf_url": row["pdf_url"],
                "md_path": row["markdown_path"]
            })
        return {"results": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/arxiv/crawl")
async def crawl_arxiv(query: SearchQuery):
    """Crawl ArXiv papers"""
    # In a real implementation, this would trigger a crawl
    # For now just return success since we're using pre-crawled data
    return {"status": "success"} 

@app.post("/api/arxiv/read")
async def read_arxiv(papers: List[PaperInfo]):
    """Request LLM to read ArXiv papers"""
    # In a real implementation, this would trigger LLM processing
    # For now just return success since we're using pre-generated summaries
    return {"status": "success"}

# File serving endpoints
@app.get("/papers/{source}/{paper_id}/pdf")
async def serve_pdf(source: str, paper_id: str):
    df = pd.read_csv(f"data/{source}/meta_paper.csv")
    df = df[df['paper_id'] == paper_id]
    pdf_filepath = df['pdf_filepath'].tolist()[0]
    """Serve PDF file for a paper"""
    path = pdf_filepath
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="PDF not found")

@app.get("/papers/{source}/{paper_id}/summary")
async def serve_summary(source: str, paper_id: str):
    """Serve markdown summary for a paper"""
    df = pd.read_csv(f"data/{source}/meta_paper.csv")
    df = df[df['paper_id'] == paper_id]
    md_name = df['markdown_path'].tolist()[0].split('/')[-1]
    path = f"outputs/{source}/report_files/{md_name}"
    print(path)
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Summary not found")
