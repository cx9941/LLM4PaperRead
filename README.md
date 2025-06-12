# PaperRead Crew

**PaperRead Crew** 是一个基于 [crewAI](https://github.com/crewAIInc/crewAI) 多智能体框架构建的科研辅助系统，旨在自动化实现两个主要任务：

1. **经典文献回顾**：聚焦领域内的高引用量论文，基于 Semantic Scholar API 抓取数据并下载 PDF。
2. **arXiv 最新论文速读**：快速抓取并阅读前沿 arXiv 论文，提取关键内容生成报告。

所有论文将通过 [Marker-PDF](https://github.com/roborovski/marker) 转换为结构化的 Markdown 文件，并由智能体系统协作分析生成解读报告。

---

## 📚 目录

- [🎯 项目亮点](#-项目亮点)
- [📦 安装与依赖](#-安装与依赖)
- [📁 项目目录结构](#-项目目录结构)
- [🚀 快速开始](#-快速开始)
- [🤖 多智能体协作框架：crewAI](#-多智能体协作框架crewai)
- [📚 示例报告](#-示例报告)
- [📮 致谢](#-致谢)

---

## 🎯 项目亮点

- 🔍 **文献双通道获取**：支持从 Semantic Scholar 和 arXiv 获取 PDF 并自动解析。
- 🧠 **多智能体分析系统**：基于 `crewAI` 多智能体协作框架，自动完成论文摘要、方法提炼、实验分析及审稿点评。
- 📄 **Markdown 格式输出**：论文转换为 Markdown 文本，便于后续加工、归档与展示。
- ⚙️ **结构清晰、可拓展性强**：代码模块清晰，支持多主题、批量处理与日志追踪。

---

## 📦 安装与依赖

### ✅ 环境要求

- Python 版本：`>=3.10, <3.14`

### 🔧 安装依赖

```bash
pip install -r requirement.txt
```

---

## 📁 项目目录结构

```
PaperRead-Crew/
├── data/
│   ├── arxiv/                        # arXiv论文数据
│   │   ├── markdown_files/          # PDF转换后的Markdown文件
│   │   ├── meta_paper.csv           # 元信息CSV
│   │   ├── meta_paper.jsonl         # 元信息JSONL
│   │   └── pdf_files/               # 原始PDF文件
│   └── semantic/                    # 经典论文数据（Semantic Scholar）
│       ├── markdown_files/
│       ├── meta_paper.csv
│       ├── meta_paper.jsonl
│       └── pdf_files/
├── input.txt                        # 查询关键词列表
├── outputs/
│   ├── arxiv/
│   │   ├── log_files/               # 抓取与解析日志
│   │   └── report_files/            # 最终阅读报告
│   └── semantic/
│       ├── log_files/
│       └── report_files/
├── paper_crawler/
│   ├── arxiv_crawler.py             # arXiv 论文爬取脚本
│   └── semantic_crawler.py          # Semantic Scholar 论文爬取脚本
├── paper_read/
│   ├── knowledge/
│   │   └── user_preference.txt      # 用户阅读偏好配置
│   ├── pyproject.toml
│   ├── src/
│   │   └── paper_read/
│   └── tests/
├── README.md                        # 本文件
└── requirement.txt                  # Python 依赖列表
```

---

## 🚀 快速开始

### 1️⃣ 抓取论文（根据关键词）

```bash
# 抓取经典论文（Semantic Scholar）
python paper_crawler/semantic_crawler.py

# 抓取最新论文（arXiv）
python paper_crawler/arxiv_crawler.py
```

### 2️⃣ 阅读并生成报告

```bash
# 运行 crewAI 智能体生成论文阅读报告
python paper_read/src/paper_read/main.py
```

- 最终报告将输出至：
  - `outputs/arxiv/report_files/`
  - `outputs/semantic/report_files/`

---

## 🤖 多智能体协作框架：crewAI

本项目基于 [crewAI](https://github.com/crewAIInc/crewAI) 实现智能体之间的角色分工与协作，涵盖如下典型角色：

- **研究员（Researcher）**：抓取与整理论文相关信息
- **报告分析员（Reporting Analyst）**：负责将分析结构化、生成Markdown报告
- **审稿人（Reviewer）**：模拟评审，给出评价与改进建议

框架遵循 [MIT License](https://github.com/crewAIInc/crewAI/blob/main/LICENSE)，开放可扩展。

---

## 📚 示例报告

运行后将在报告目录中生成如下结构的报告文件（Markdown 格式）：

```markdown
# Paper Title

## 一、研究动机与背景

## 二、方法与模型描述（含公式）

## 三、实验设置与结果分析

## 四、亮点与不足（评审视角）

## 五、总结与影响力评估
```

---

## 📮 致谢

如需帮助或反馈建议，请访问：

感谢Crew AI的框架支持

---