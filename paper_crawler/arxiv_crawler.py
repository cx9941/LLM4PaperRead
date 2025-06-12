import arxiv
import os
import requests
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import argparse
import json
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

# 初始化 Marker 转换器
converter = PdfConverter(artifact_dict=create_model_dict())

def process_query(query, max_results, base_dir):
    query_time = datetime.now().strftime("%Y-%m-%d")
    pdf_dir = os.path.join(base_dir, "pdf_files")
    md_dir = os.path.join(base_dir, "markdown_files")
    meta_path = os.path.join(base_dir, "meta_paper.csv")

    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)

    client = arxiv.Client()

    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    results = list(client.results(search))
    records = []

    if os.path.exists(meta_path):
        paper_id_list = pd.read_csv(meta_path)['paper_id'].tolist()
    else:
        paper_id_list = []


    for result in tqdm(results, desc=f"Query: {query}", total=len(results)):
        try:
            title = result.title.strip().replace("\n", " ")
            paper_id = result.get_short_id()
            if paper_id in paper_id_list:
                continue
            pdf_url = result.pdf_url
            authors = ", ".join([author.name for author in result.authors])
            categories = ", ".join(result.categories)
            comment = result.comment if result.comment else ""
            summary = result.summary
            publication_date = result.published.strftime("%Y-%m-%d")
            safe_title = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in title[:50])
            pdf_filename = f"{publication_date}_{safe_title}.pdf"
            md_filename = f"{publication_date}_{safe_title}.md"
            pdf_filepath = os.path.join(pdf_dir, pdf_filename)
            md_filepath = os.path.join(md_dir, md_filename)

            # 下载 PDF
            if not os.path.exists(pdf_filepath):
                pdf_response = requests.get(pdf_url)
                with open(pdf_filepath, "wb") as f:
                    f.write(pdf_response.content)

                # Marker 转 Markdown
                try:
                    rendered = converter(pdf_filepath)
                    text, _, _ = text_from_rendered(rendered)
                    with open(md_filepath, "w", encoding="utf-8") as w:
                        w.write(text)
                except Exception as e:
                    print(f"⚠️ Markdown 生成失败: {pdf_filename}，错误: {e}")
                    md_filepath = ""

            # 元数据记录
            record = {
                "query_date": query_time,
                "query_keyword": query,
                "paper_id": paper_id,
                "publication_date": result.published.strftime("%Y-%m-%d"),
                "updated_date": result.updated.strftime("%Y-%m-%d"),
                "title": title,
                "authors": authors,
                "abstract": summary,
                "primary_category": result.primary_category,
                "categories": categories,
                "comment": comment,
                "pdf_url": pdf_url,
                "pdf_filename": pdf_filename,
                "markdown_path": md_filepath,

            }
            records.append(record)
            print(f"✅ 爬取论文: {title[:60]}")
        except Exception as e:
            print(f"❌ 跳过论文: {title[:60]}... 错误: {e}")

    # 保存元数据
    if records:
        df = pd.DataFrame(records).drop('abstract', axis=1)
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
    parser.add_argument("--keywords_file", type=str, help="关键词文件路径（mode=file）", default="input.txt")
    parser.add_argument("--keywords", type=str, help="逗号分隔关键词（mode=inline）")
    parser.add_argument("--max_results", type=int, default=50, help="每个关键词最大论文数")
    parser.add_argument("--base_dir", type=str, default="data/arxiv", help="保存根目录")
    args = parser.parse_args()

    if args.mode == "file":
        if not args.keywords_file or not os.path.exists(args.keywords_file):
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
