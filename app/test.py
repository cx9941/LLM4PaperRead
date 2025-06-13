import pytest
from fastapi.testclient import TestClient
from main import app
import os
import pandas as pd

client = TestClient(app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Paper Daily" in response.text

def test_classic_page():
    response = client.get("/classic")
    assert response.status_code == 200
    assert "Classic Papers" in response.text

def test_latest_page():
    response = client.get("/latest")
    assert response.status_code == 200
    assert "Latest Papers" in response.text

def test_semantic_search():
    # Test with valid query
    response = client.post(
        "/api/semantic/search",
        json={"query": "Open-set semi Supervised Learning"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    
    # Test empty query
    response = client.post(
        "/api/semantic/search",
        json={"query": ""}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0

def test_arxiv_search():
    # Test with valid query
    response = client.post(
        "/api/arxiv/search",
        json={"query": "LLM"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0

def test_semantic_crawl():
    response = client.post(
        "/api/semantic/crawl",
        json={"query": "test"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_arxiv_crawl():
    response = client.post(
        "/api/arxiv/crawl",
        json={"query": "test"}
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_semantic_read():
    test_paper = {
        "id": "test_id",
        "title": "Test Paper",
        "authors": ["Author 1", "Author 2"],
        "abstract": "Test abstract",
        "pdf_url": "http://example.com/test.pdf",
        "md_path": "data/semantic/markdown_files/test.md"
    }
    response = client.post(
        "/api/semantic/read",
        json=[test_paper]
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_arxiv_read():
    test_paper = {
        "id": "test_id",
        "title": "Test Paper",
        "authors": ["Author 1", "Author 2"],
        "abstract": "Test abstract",
        "pdf_url": "http://example.com/test.pdf",
        "md_path": "outputs/arxiv/report_files/test.md"
    }
    response = client.post(
        "/api/arxiv/read",
        json=[test_paper]
    )
    assert response.status_code == 200
    assert response.json() == {"status": "success"}

def test_serve_pdf():
    # Create a dummy PDF file for testing
    test_pdf_path = "data/semantic/pdf_files/test.pdf"
    os.makedirs(os.path.dirname(test_pdf_path), exist_ok=True)
    with open(test_pdf_path, "wb") as f:
        f.write(b"test pdf content")
    
    response = client.get("/papers/semantic/test/pdf")
    assert response.status_code == 200
    assert response.content == b"test pdf content"
    
    # Clean up
    os.remove(test_pdf_path)

def test_serve_summary():
    # Create a dummy markdown file for testing
    test_md_path = "data/semantic/markdown_files/test.md"
    os.makedirs(os.path.dirname(test_md_path), exist_ok=True)
    with open(test_md_path, "w") as f:
        f.write("test markdown content")
    
    response = client.get("/papers/semantic/test/summary")
    assert response.status_code == 200
    assert response.text == "test markdown content"
    
    # Clean up
    os.remove(test_md_path)

def test_serve_nonexistent_pdf():
    response = client.get("/papers/semantic/nonexistent/pdf")
    assert response.status_code == 404
    assert response.json() == {"detail": "PDF not found"}

def test_serve_nonexistent_summary():
    response = client.get("/papers/semantic/nonexistent/summary")
    assert response.status_code == 404
    assert response.json() == {"detail": "Summary not found"}
