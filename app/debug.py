import pandas as pd
import json

query = 'Category Discovery'


"""Search Semantic Scholar papers"""

df = pd.DataFrame([json.loads(i) for i in open("data/semantic/meta_paper.jsonl", 'r').readlines()])

# Simple keyword search in title and abstract
mask = (df['title'].str.contains(query, case=False)) | \
        (df['abstract'].str.contains(query, case=False))
results = df[mask].to_dict('records')

print(results)
    
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
papers