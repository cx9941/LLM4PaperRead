from langchain_openai import ChatOpenAI

import os
os.environ["OPENAI_API_BASE"] = "https://uni-api.cstcloud.cn/v1"
manager_llm = ChatOpenAI(model="openai/deepseek-v3:671b")
executor_llm = ChatOpenAI(model="openai/deepseek-v3:671b")
