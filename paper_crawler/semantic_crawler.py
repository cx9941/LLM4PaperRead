import os
import requests
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import argparse
from semanticscholar import SemanticScholar
import json
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# 初始化 Marker 转换器
converter = PdfConverter(artifact_dict=create_model_dict())
sch = SemanticScholar()

def safe_filename(text, max_length=50):
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in text[:max_length])

def process_query(query, max_results, base_dir):
    query_time = datetime.now().strftime("%Y-%m-%d")
    pdf_dir = os.path.join(base_dir, "pdf_files")
    md_dir = os.path.join(base_dir, "markdown_files")
    meta_path = os.path.join(base_dir, "meta_paper.csv")

    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)

    try:
        results = sch.search_paper(query, limit=max_results)
    except Exception as e:
        print(f"❌ 查询失败: {query}，错误: {e}")
        return

    records = []
    if os.path.exists(meta_path):
        paper_id_list = pd.read_csv(meta_path)['paper_id'].tolist()
    else:
        paper_id_list = []

    for result in tqdm(results[:max_results], desc=f"Query: {query}", total=max_results):
        try:
            paper_id = result._paperId
            if paper_id in paper_id_list:
                continue
            title = result.title.strip().replace("\n", " ")
            authors = ", ".join([_['name'] for _ in result._authors])
            citation_count = result.citationCount
            influentialCitationCount = result.influentialCitationCount
            venue = result._venue

            try:
                publication_date = result._publicationDate.strftime("%Y-%m-%d")
            except Exception as e:
                publication_date = str(result._year)
            abstract = result.abstract
            arxiv_id = result.externalIds["ArXiv"] if "ArXiv" in result.externalIds else None
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else ""
            pdf_url = result._openAccessPdf['url'] if result._openAccessPdf['url'] != "" else pdf_url

            safe_title = safe_filename(title)
            pdf_filename = f"{publication_date}_{safe_title}.pdf"
            md_filename = pdf_filename.replace(".pdf", ".md")
            pdf_filepath = os.path.join(pdf_dir, pdf_filename)
            md_filepath = os.path.join(md_dir, md_filename)

            # 下载 PDF（如有 arXiv 链接）
            if arxiv_id:
                if not os.path.exists(pdf_filepath):
                    pdf_response = requests.get(pdf_url)
                    with open(pdf_filepath, "wb") as f:
                        f.write(pdf_response.content)

                if not os.path.exists(md_filepath):
                    rendered = converter(pdf_filepath)
                    text, _, _ = text_from_rendered(rendered)
                    with open(md_filepath, "w", encoding="utf-8") as w:
                        w.write(text)

            record = {
                "query_date": query_time,
                "query_keyword": query,
                "paper_id": paper_id,
                "publication_date": publication_date,
                "title": title,
                "authors": authors,
                "venue": venue,
                "citation_count": citation_count,
                "influential_citation_count": influentialCitationCount,
                "abstract": abstract,
                "pdf_url": pdf_url,
                "pdf_filename": pdf_filename if arxiv_id else "",
                "markdown_path": md_filepath if arxiv_id else ""
            }
            records.append(record)

        except Exception as e:
            print(f"❌ 跳过论文: {title[:60]} 错误: {e}")

    # 保存元数据
    if records:
        df = pd.DataFrame(records).drop(['abstract'], axis=1)
        if os.path.exists(meta_path):
            df.to_csv(meta_path, mode='a', header=False, index=False)
        else:
            df.to_csv(meta_path, index=False)
        print(f"✅ 元数据已保存至 {meta_path}")
    else:
        print(f"⚠️ 没有下载任何论文: {query}")

    with open(meta_path.replace('csv', 'jsonl'), 'a') as f:
        for item in records:
            json.dump(item, f)
            f.write('\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="file", choices=["file", "inline"], help="关键词模式")
    parser.add_argument("--keywords_file", type=str, default="input.txt", help="关键词文件路径（mode=file）")
    parser.add_argument("--keywords", type=str, help="逗号分隔关键词（mode=inline）")
    parser.add_argument("--max_results", type=int, default=50, help="每个关键词最大论文数")
    parser.add_argument("--base_dir", type=str, default="data/semantic", help="保存根目录")
    args = parser.parse_args()

    if args.mode == "file":
        if not os.path.exists(args.keywords_file):
            raise ValueError("关键词文件路径无效")
        with open(args.keywords_file, "r", encoding="utf-8") as f:
            keyword_list = [line.strip() for line in f if line.strip()]
    elif args.mode == "inline":
        if not args.keywords:
            raise ValueError("请通过 --keywords 传入关键词")
        keyword_list = [kw.strip() for kw in args.keywords.split(",") if kw.strip()]
    else:
        raise ValueError("无效的模式选择")

    for kw in keyword_list:
        process_query(query=kw, max_results=args.max_results, base_dir=args.base_dir)

if __name__ == "__main__":
    main()