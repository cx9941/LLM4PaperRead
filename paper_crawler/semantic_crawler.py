import os
os.environ['CUDA_VISIBLE_DEVICES'] = '4'
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
from bs4 import BeautifulSoup
import requests
from xml.etree import ElementTree as ET
import re
from urllib.parse import urljoin
import nest_asyncio

# 初始化 Marker 转换器
converter = PdfConverter(artifact_dict=create_model_dict())

def safe_filename(text, max_length=100):
    return "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in text[:max_length])

def fetch_url_response(pdf_url):
    if 'aaai' in pdf_url:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
            "Referer": pdf_url,
        }
        response = requests.get(pdf_url.replace('view', 'download'), headers=headers)
    else:
        response = requests.get(pdf_url)
    return response


def fetch_doi_pdf_url(doi_url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # 第一步：获取跳转后的页面
    try:
        response = requests.get(doi_url, headers=headers, allow_redirects=True, timeout=10)
        final_url = response.url
        print("跳转后URL：", final_url)
    except requests.exceptions.RequestException as e:
        print("请求失败：", e)
        return None

    # 第二步：尝试从最终页面中解析 PDF 链接
    soup = BeautifulSoup(response.text, "html.parser")

    # 常见PDF链接关键词
    pdf_keywords = ["pdf", ".pdf"]
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if any(k in href.lower() for k in pdf_keywords) or a_tag.text.strip('\n\t') == 'PDF':
            if href.startswith("/"):
                href = final_url.rstrip("/") + href
            elif href.startswith("http"):
                pass
            else:
                href = final_url.rstrip("/") + "/" + href
            print("发现可能的PDF链接：", href)
            return href
    return None


def fetch_dblp_pdf_url(bibkey):
    url = f"https://dblp.org/rec/{bibkey}.xml"
    response = fetch_url_response(url)

    link_html = re.findall(r'<ee type="oa">(.*)</ee>', response.text)
    if len(link_html) == 0:
        link_html = re.findall(r'<ee>(.*)</ee>', response.text)
    link_html = link_html[0]
    if len(link_html) == 1:
        return None
    # pdf_response = requests.get(link_html)
    pdf_response = fetch_url_response(link_html)
    soup = BeautifulSoup(pdf_response.text, "html.parser")
    pdf_keywords = ["pdf", ".pdf"]
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if any(k in href.lower() for k in pdf_keywords):
            if href.startswith("/"):
                href = urljoin(pdf_response.url, href)
            print("发现可能的PDF链接：", href)
            return href
    return None


def fetch_url(result, pdf_filepath, md_filepath):
    try:
        pdf_url = None
        for mode_type in ['ArXiv', 'DOI', 'DBLP', '']:
            if mode_type not in result.externalIds:
                continue
            paper_id = result.externalIds[mode_type]
            if mode_type == 'ArXiv':
                pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
            elif mode_type == 'DOI':
                doi_url = f"https://doi.org/{paper_id}"
                pdf_url = fetch_doi_pdf_url(doi_url)
            elif mode_type == 'DBLP':
                pdf_url = fetch_dblp_pdf_url(paper_id)
            else:
                pdf_url = result._openAccessPdf['url']
            if pdf_url is not None:
                # pdf_response = requests.get(pdf_url)
                pdf_response = fetch_url_response(pdf_url)
                if pdf_response.status_code == 200:
                    break
                else:
                    pdf_url = None
    except Exception as e:
        print(f"This paper {result.title} PDF can not be found. Error: ", e)
    
    if pdf_url is not None:
        try:
            if not os.path.exists(pdf_filepath):
                # pdf_response = requests.get(pdf_url)
                pdf_response = fetch_url_response(pdf_url)
                with open(pdf_filepath, "wb") as f:
                    f.write(pdf_response.content)

            if not os.path.exists(md_filepath):
                rendered = converter(pdf_filepath)
                text, _, _ = text_from_rendered(rendered)
                with open(md_filepath, "w", encoding="utf-8") as w:
                    w.write(text)
        except Exception as e:
            print(f'PDF {pdf_url}, doanload Error:', e)
            pdf_url = None
    return pdf_url



def process_query(query, max_results, base_dir):
    # Initialize SemanticScholar client inside function to avoid import-time loop patching
    # try:
    #     nest_asyncio.apply()
    #     sch = SemanticScholar()
    # except Exception as e:
    #     print(f"Failed to initialize SemanticScholar client: {e}")
    #     return

    sch = SemanticScholar()
    query_time = datetime.now().strftime("%Y-%m-%d")
    pdf_dir = os.path.join(base_dir, "pdf_files")
    md_dir = os.path.join(base_dir, "markdown_files")
    meta_path = os.path.join(base_dir, "meta_paper.csv")

    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(md_dir, exist_ok=True)

    try:
        results = sch.search_paper(query, sort='citationCount')
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
            safe_title = safe_filename(title)
            pdf_filename = f"{publication_date}_{safe_title}.pdf"
            md_filename = pdf_filename.replace(".pdf", ".md")
            pdf_filepath = os.path.join(pdf_dir, pdf_filename)
            md_filepath = os.path.join(md_dir, md_filename)
            pdf_url = fetch_url(result, pdf_filepath, md_filepath)
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
                "pdf_filepath": pdf_filepath if pdf_url is not None else "",
                "markdown_path": md_filepath if pdf_url is not None else ""
            }
            records.append(record)

        except Exception as e:
            print(f"❌ 跳过论文: {title[:60]} 错误: {e}")

    # 保存元数据
    if records:
        df = pd.DataFrame(records).drop(['abstract'], axis=1)
        # df = df[df['pdf_url'].apply(len) > 1]
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
    parser.add_argument("--max_results", type=int, default=100, help="每个关键词最大论文数")
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
