from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
import os
import pandas as pd
import json
import asyncio
import pandas as pd
from fastapi import BackgroundTasks
app = FastAPI()

# Set up static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

class SearchQuery(BaseModel):
    query: str
    max_results: Optional[int] = 50

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
    try:
        df = pd.DataFrame([json.loads(i) for i in open("data/semantic/meta_paper.jsonl", 'r').readlines()])
        df = df[df['pdf_url'].apply(lambda x: type(x) == type(''))]
        if query.query:
            # Simple keyword search in title and abstract
            # mask = (df['title'].str.contains(query.query, case=False)) | (df['abstract'].str.contains(query.query, case=False))
            mask = df['query_keyword'] == query.query
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
                "md_path": row["markdown_path"],
                "venue": row.get("venue", ""),
                "citation_count": row["citation_count"],
                "publication_date": row.get("publication_date", "")
            })
        return {"results": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ArXiv Endpoints 
@app.post("/api/arxiv/search")
async def search_arxiv(query: SearchQuery):
    """Search ArXiv papers"""
    try:
        df = pd.DataFrame([json.loads(i) for i in open("data/semantic/meta_paper.jsonl", 'r').readlines()])
        df = df[df['pdf_url'].apply(lambda x: type(x) == type(''))]
        if query.query:
            # Simple keyword search in title and abstract
            # mask = (df['title'].str.contains(query.query, case=False)) | (df['abstract'].str.contains(query.query, case=False))
            mask = df['query_keyword'] == query.query
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
                "md_path": row["markdown_path"],
                "venue": "arXiv",
                "publication_date": row.get("publication_date", "")
            })
        return {"results": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/semantic/crawl")
async def crawl_semantic(query: SearchQuery):
    """Crawl Semantic Scholar papers with progress updates"""
    from paper_crawler.semantic_crawler import process_query
    process_query(query.query,
        max_results=100,
        base_dir='data/semantic'
    )
    return {"status": "success"}

@app.post("/api/arxiv/crawl")
async def crawl_semantic(query: SearchQuery):
    """Crawl Semantic Scholar papers with progress updates"""
    from paper_crawler.arxiv_crawler import process_query
    process_query(query.query,
        max_results=10,
        base_dir='data/arxiv'
    )
    return {"status": "success"}


@app.post("/api/arxiv/read")
async def read_arxiv(papers: List[PaperInfo]):
    """Request LLM to read ArXiv papers"""

    return {"status": "success"}


def background_read_semantic(paper_id_list: List[str]):
    import os
    import sys
    sys.path.append('/ssd/chenxi/projects/paper_daily/paper_read/src/paper_read')
    import pandas as pd
    from paper_read.src.paper_read.main import process_paper

    df = pd.read_csv("data/semantic/meta_paper.csv")
    df = df[df['paper_id'].isin(paper_id_list)]

    import asyncio
    semaphore = asyncio.Semaphore(5)

    success_ids = []
    failed_ids = []
    errors = []

    async def async_process(row):
        async with semaphore:
            paper_id = row["paper_id"]
            try:
                await asyncio.to_thread(process_paper, row, 'semantic', False)
                success_ids.append(paper_id)
            except Exception as e:
                failed_ids.append(paper_id)
                errors.append({
                    "paper_id": paper_id,
                    "error": str(e)
                })

    async def run_all():
        await asyncio.gather(*[async_process(row) for _, row in df.iterrows()])
        # 写入日志或文件
        with open("logs/semantic_read.log", "a") as f:
            f.write(f"Processed: {success_ids}, Failed: {failed_ids}\n")

    asyncio.run(run_all())

@app.post("/api/semantic/read")
async def read_semantic(papers: List[PaperInfo], background_tasks: BackgroundTasks):
    print('hello')
    paper_id_list = [i.id for i in papers]
    background_tasks.add_task(background_read_semantic, paper_id_list)
    return {"status": "started", "message": "Processing started in background."}

# File serving endpoints
@app.get("/papers/{source}/{paper_id}/pdf")
async def serve_pdf(source: str, paper_id: str):
    print('hello')
    df = pd.DataFrame([json.loads(i) for i in open(f"data/{source}/meta_paper.jsonl", 'r').readlines()])
    df = df[df['paper_id'] == paper_id]
    if len(df) == 0:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    pdf_filepath = df['pdf_filepath'].values[0]
    if os.path.exists(pdf_filepath):
        return FileResponse(pdf_filepath)
    raise HTTPException(status_code=404, detail="PDF not found")

@app.get("/papers/{source}/{paper_id}/summary", response_class=HTMLResponse)
async def summary_viewer(request: Request, source: str, paper_id: str):
    # 获取论文元数据
    df = pd.DataFrame([json.loads(i) for i in open(f"data/{source}/meta_paper.jsonl", 'r').readlines()])
    df = df[df['paper_id'] == paper_id]
    if len(df) == 0:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # 构建markdown文件路径
    md_filename = df['markdown_path'].values[0].split('/')[-1]
    md_path = f'outputs/{source}/report_files/{md_filename}'
    
    # 读取markdown内容
    summary_content = ""
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            summary_content = f.read()
    
    return templates.TemplateResponse("summary_viewer.html", {
        "request": request,
        "source": source,
        "paper_id": paper_id,
        "summary_content": summary_content,
        "title": df['title'].values[0]
    })
