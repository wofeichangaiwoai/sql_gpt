# Introduction
sql_gpt is a powerful tool that can generate SQL queries that meet your requirements through simple text 
descriptions. it is based on DIN_SQL and langchain framework. you can choose llama models or chatgpt as 
you like. 

# Feature List
✅Automatic SQL Query Generation: Simply describe your query in text, and the tool will automatically generate the SQL query that meets your requirements.
✅Intergration with multi acceleration framework:Intergrate with multi framework (llamacpp/vllm/tgi) in order to save gpu resources.
✅llm Route: Use few-shot learning to detect the questions user ask belongs to sql question or general question.

# Quick Start Guide
1. pip install -r requirements.txt
2. Configure your database connection information, including hostname, username, password, etc. for database interaction.
3. Configure tgi image if you want to use tgi framework.
4. If you want to use DIN-sql, execute the command:  PYTHONPATH=. LLM_TYPE=din python unix/common/answer.py
   If you want to use langchain sqlchain, execute the command:  PYTHONPATH=. LLM_TYPE=vllm python unix/common/answer.py

