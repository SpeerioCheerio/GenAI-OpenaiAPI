# nl2sql_app.py

import os
import re

from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotChatMessagePromptTemplate,
    PromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser

# Import schema and few-shot examples
from schema import schema_reference
from few_shots import examples

# 1. CONFIGURATION
os.environ["OPENAI_API_KEY"] = "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"
DB_USER     = "root"
DB_PASSWORD = "Aes2024358.."
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_NAME     = "classicmodels"

# 2. CONNECT, embedding schema for context
uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
db = SQLDatabase.from_uri(
    uri,
    custom_table_info={DB_NAME: schema_reference}
)

# 3. LLM & Tools
llm = ChatOpenAI(model="gpt-4o", temperature=0)
execute_query = QuerySQLDatabaseTool(db=db)

# 4. Build few-shot prompt
#   a) Template for each example
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}\nSQLQuery:"),
    ("ai", "{query}")
])
#   b) Few-shot wrapper
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
    input_variables=["input"]
)

# (1) Your usual system instructions
system_prompt = (
    "You are a MySQL expert. Given a natural language question, "
    "produce ONLY the SQL needed—no prefixes, no code fences, no extra explanation."
)

# (2) Inject the schema via the built-in placeholders
schema_prompt = "Here is the database schema (you may refer to up to {top_k} tables):\n{table_info}"

# (3) Put it all together, declaring all three variables:
final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("system", schema_prompt),
        ("user", "{input}"),
    ],
    input_variables=["input", "table_info", "top_k"],
)

# (4) Now LangChain will be happy:
generate_query = create_sql_query_chain(llm, db, prompt=final_prompt)


# 7. Rephrase template for SELECT results
rephrase_prompt = PromptTemplate.from_template(
    "Given the question, SQL query, and result, answer conversationally:\n\n"
    "Question: {question}\n"
    "SQL Query: {query}\n"
    "SQL Result: {result}\n\n"
    "Answer:"
)
rephrase_answer = rephrase_prompt | llm | StrOutputParser()

# 8. SQL extractor
SQL_RE = re.compile(r"(?i)\b(SELECT|WITH|SHOW|INSERT|UPDATE|DELETE)\b")
def extract_sql(text: str) -> str:
    # strip fences
    if text.strip().startswith("```"):
        parts = text.strip().split("```")
        text = "\n".join(parts[1:-1])
    # strip prefixes
    text = text.replace("SQLQuery:", "").replace("SQL:", "").strip()
    # find real SQL
    m = SQL_RE.search(text)
    sql = text[m.start():].strip("`; \n") if m else text.strip("`; \n")
    return sql + ";"

def is_dml(sql: str) -> bool:
    return sql.strip().upper().startswith(("INSERT", "UPDATE", "DELETE"))

# 9. Interactive loop
print("Ask anything (type 'exit' to quit):")
while True:
    q = input(">> ").strip()
    if q.lower() in ("exit", "quit"):
        break

    # a) Generate SQL
    raw_sql = generate_query.invoke({"input": q})
    print("\nRaw SQL:\n", raw_sql)

    # b) Clean & extract
    sql = extract_sql(raw_sql)
    print("\nCleaned SQL:\n", sql)

    try:
        if is_dml(sql):
            confirm = input("⚠️ This will modify data. Execute? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("Cancelled.\n")
                continue
            result = execute_query.invoke(sql)
            print("\n✅ Modification result:\n", result, "\n")
        else:
            rows = execute_query.invoke(sql)
            print("\nRaw Result:\n", rows)
            answer = rephrase_answer.invoke({
                "question": q,
                "query": sql,
                "result": rows
            })
            print("\nAnswer:\n", answer, "\n")

    except Exception as e:
        print("Error:", e, "\n")
