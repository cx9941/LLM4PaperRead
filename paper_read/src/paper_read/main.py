#!/usr/bin/env python
import sys
import warnings
import os
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path
from paper_crew import PaperRead

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Configuration
OUTPUT_BASE_DIR = "outputs"
META_PATHS = {
    'arxiv': "data/arxiv/meta_paper.csv",
    'semantic': "data/semantic/meta_paper.csv"  # Assuming similar structure for semantic scholar
}
MARKDOWN_DIRS = {
    'arxiv': "data/arxiv/markdown_files",
    'semantic': "data/semantic/markdown_files"
}

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Process research papers")
    parser.add_argument('--type', choices=['arxiv', 'semantic'], default='arxiv',
                       help="Type of papers to process (arxiv or semantic)")
    parser.add_argument('--keyword', default='Multi-Agent LLM',
                       help="Keyword to filter papers (e.g., 'Multi-Agent LLM')")
    parser.add_argument('--force', action='store_true',
                       help="Force reprocessing even if output exists")
    return parser.parse_args()

def ensure_output_dir(output_dir):
    """Ensure output directory exists"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

def get_processed_papers(output_dir):
    """Get set of already processed papers based on existing output files"""
    processed = set()
    if os.path.exists(output_dir):
        for filename in os.listdir(output_dir):
            if filename.endswith(".json"):
                processed.add(filename.replace(".json", ""))
    return processed

def process_paper(row, paper_type, force_process=False):
    """Process a single paper"""
    paper_id = f"{paper_type}_{row['arxiv_id'].replace('/', '_')}" if paper_type == 'arxiv' else f"{paper_type}_{row['paper_id']}"
    output_filename = row['markdown_path'].replace('data', 'outputs').replace('markdown_files', 'log_files').replace('md', 'json')
    report_file = row['markdown_path'].replace('data', 'outputs').replace('markdown_files', 'report_files')
    
    # Skip if already processed and not forcing
    if not force_process and os.path.exists(output_filename):
        print(f"Skipping already processed paper: {row['title']}")
        return
    
    # Check if markdown file exists
    markdown_path = row['markdown_path']
    if not os.path.exists(markdown_path):
        print(f"Markdown file not found for {row['title']} at {markdown_path}")
        return
    
    # Read markdown content
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading markdown file {markdown_path}: {e}")
        return
    
    # Prepare inputs
    inputs = {
        'topic': row['query_keyword'],
        'title': row['title'],
        'abstract': row.get('abstract', ""),  # Some sources might have abstract
        'content': content,
        'paper_id': paper_id,
        'authors': row['authors'],
        'publication_date': row['publication_date'],
        'source': paper_type
    }
    
    # Process the paper
    print(f"Processing {paper_type} paper: {row['title']}")
    try:
        args = {
            "output_log_file": output_filename,
            "report_file": report_file,
        }
        result = PaperRead(args).crew().kickoff(inputs=inputs)
        # Save result
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Successfully processed and saved: {output_filename}")
    except Exception as e:
        print(f"Error processing paper {row['title']}: {e}")

def run():
    """Run the crew for selected papers"""
    args = parse_arguments()
    
    output_dir = f"{OUTPUT_BASE_DIR}/{args.type}"
    ensure_output_dir(output_dir)
    
    try:
        # Load metadata
        df = pd.read_csv(META_PATHS[args.type])
        
        # Filter by keyword
        keyword_filter = df['query_keyword'] == args.keyword
        filtered_df = df[keyword_filter]
        
        if len(filtered_df) == 0:
            print(f"No papers found for keyword: {args.keyword}")
            return
        
        print(f"Found {len(filtered_df)} papers for keyword '{args.keyword}' in {args.type}")
        
        # Get processed papers if not forcing
        processed_papers = set() if args.force else get_processed_papers(output_dir)
        
        for _, row in filtered_df.iterrows():
            paper_id = f"{args.type}_{row['arxiv_id'].replace('/', '_')}" if args.type == 'arxiv' else f"{args.type}_{row['paper_id']}"
            if paper_id not in processed_papers:
                process_paper(row, args.type, args.force)
            
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

def train():
    inputs = {
        "title": "你的论文标题",
        "abstract": "摘要信息",
        "content": "完整内容"
    }
    try:
        PaperRead().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    try:
        PaperRead().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    inputs = {
        "title": "你的论文标题",
        "abstract": "摘要信息",
        "content": "正文内容"
    }
    try:
        PaperRead().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == '__main__':
    run()