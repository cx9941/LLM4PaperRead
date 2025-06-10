# PaperRead Crew

Welcome to the PaperRead Crew project, powered by [crewAI](https://crewai.com). This template is designed to help you set up a multi-agent AI system with ease, leveraging the powerful and flexible framework provided by crewAI. Our goal is to enable your agents to collaborate effectively on complex tasks, maximizing their collective intelligence and capabilities.

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, install:

```bash
pip install requirement.txt
```

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

To crawl papers, you need to run
```
python paper_crawler/semantic_crawler.py
python paper_crawler/arxiv_crawler.py
```

Then read the paper further
```
python paper_read/src/paper_read/main.py
```

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Support

For support, questions, or feedback regarding the PaperRead Crew or crewAI.
- Visit our [documentation](https://docs.crewai.com)
- Reach out to us through our [GitHub repository](https://github.com/joaomdmoura/crewai)
- [Join our Discord](https://discord.com/invite/X4JWnZnxPb)
- [Chat with our docs](https://chatg.pt/DWjSBZn)

Let's create wonders together with the power and simplicity of crewAI.
