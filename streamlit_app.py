import streamlit as st
import os
import re

from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Configure environment and credentials
os.environ["OPENAI_API_KEY"] = "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"
DB_USER     = "root"
DB_PASSWORD = "Aes2024358.."
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_NAME     = "classicmodels"

# 2. Embed your schema reference (paste full CREATE TABLE definitions here)
schema_reference = """
[Database Dialect]:
mysql

[Usable Table Names]:
['customers', 'employees', 'offices', 'orderdetails', 'orders', 'payments', 'productlines', 'products']

[Table Schema Info]:

CREATE TABLE customers (
    customerNumber INTEGER NOT NULL,
    customerName VARCHAR(50) NOT NULL,
    contactLastName VARCHAR(50) NOT NULL,
    contactFirstName VARCHAR(50) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    addressLine1 VARCHAR(50) NOT NULL,
    addressLine2 VARCHAR(50),
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50),
    postalCode VARCHAR(15),
    country VARCHAR(50) NOT NULL,
    salesRepEmployeeNumber INTEGER,
    creditLimit DECIMAL(10, 2),
    PRIMARY KEY (customerNumber),
    CONSTRAINT customers_ibfk_1 FOREIGN KEY(salesRepEmployeeNumber) 
      REFERENCES employees (employeeNumber)
) COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE employees (
    employeeNumber INTEGER NOT NULL,
    lastName VARCHAR(50) NOT NULL,
    firstName VARCHAR(50) NOT NULL,
    extension VARCHAR(10) NOT NULL,
    email VARCHAR(100) NOT NULL,
    officeCode VARCHAR(10) NOT NULL,
    reportsTo INTEGER,
    jobTitle VARCHAR(50) NOT NULL,
    PRIMARY KEY (employeeNumber),
    CONSTRAINT employees_ibfk_1 FOREIGN KEY(reportsTo) 
      REFERENCES employees (employeeNumber),
    CONSTRAINT employees_ibfk_2 FOREIGN KEY(officeCode) 
      REFERENCES offices (officeCode)
) COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE offices (
    officeCode VARCHAR(10) NOT NULL,
    city VARCHAR(50) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    addressLine1 VARCHAR(50) NOT NULL,
    addressLine2 VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50) NOT NULL,
    postalCode VARCHAR(15) NOT NULL,
    territory VARCHAR(10) NOT NULL,
    PRIMARY KEY (officeCode)
) COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE orderdetails (
    orderNumber INTEGER NOT NULL,
    productCode VARCHAR(15) NOT NULL,
    quantityOrdered INTEGER NOT NULL,
    priceEach DECIMAL(10, 2) NOT NULL,
    orderLineNumber SMALLINT NOT NULL,
    PRIMARY KEY (orderNumber, productCode),
    CONSTRAINT orderdetails_ibfk_1 FOREIGN KEY(orderNumber) 
      REFERENCES orders (orderNumber),
    CONSTRAINT orderdetails_ibfk_2 FOREIGN KEY(productCode) 
      REFERENCES products (productCode)
) COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE orders (
    orderNumber INTEGER NOT NULL,
    orderDate DATE NOT NULL,
    requiredDate DATE NOT NULL,
    shippedDate DATE,
    status VARCHAR(15) NOT NULL,
    comments TEXT,
    customerNumber INTEGER NOT NULL,
    PRIMARY KEY (orderNumber),
    CONSTRAINT orders_ibfk_1 FOREIGN KEY(customerNumber) 
      REFERENCES customers (customerNumber)
) COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE payments (
    customerNumber INTEGER NOT NULL,
    checkNumber VARCHAR(50) NOT NULL,
    paymentDate DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (customerNumber, checkNumber),
    CONSTRAINT payments_ibfk_1 FOREIGN KEY(customerNumber) 
      REFERENCES customers (customerNumber)
) COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE productlines (
    productLine VARCHAR(50) NOT NULL,
    textDescription VARCHAR(4000),
    htmlDescription MEDIUMTEXT,
    image MEDIUMBLOB,
    PRIMARY KEY (productLine)
) COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB;

CREATE TABLE products (
    productCode VARCHAR(15) NOT NULL,
    productName VARCHAR(70) NOT NULL,
    productLine VARCHAR(50) NOT NULL,
    productScale VARCHAR(10) NOT NULL,
    productVendor VARCHAR(50) NOT NULL,
    productDescription TEXT NOT NULL,
    quantityInStock SMALLINT NOT NULL,
    buyPrice DECIMAL(10, 2) NOT NULL,
    MSRP DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (productCode),
    CONSTRAINT products_ibfk_1 FOREIGN KEY(productLine) 
      REFERENCES productlines (productLine)
) COLLATE utf8mb4_0900_ai_ci DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB;
"""


@st.cache_resource
def get_db():
    uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return SQLDatabase.from_uri(uri, custom_table_info={DB_NAME: schema_reference})

db = get_db()
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
generate_query = create_sql_query_chain(llm, db)
execute_query  = QuerySQLDatabaseTool(db=db)

answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question in a clear, conversational style.

Question: {question}
SQL Query: {query}
SQL Result: {result}

Answer:"""
)
rephrase_answer = answer_prompt | llm | StrOutputParser()

def extract_sql(text: str) -> str:
    text = re.sub(r'```[^\n]*\n', '', text).replace('```', '')
    lines = [
        line for line in text.splitlines()
        if not re.match(r'^\s*(sql|SQLQuery)\s*[:\\-]?\s*$', line, re.IGNORECASE)
    ]
    cleaned = "\n".join(lines)
    m = re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|WITH)\b',
                  cleaned, re.IGNORECASE)
    sql = cleaned[m.start():] if m else cleaned
    return sql.strip().rstrip(';')

st.title("AI-Powered SQL Chat")

# Step 1: Ask user for question
with st.form("question_form"):
    st.text_input("Enter your question", key="question_input")
    question_submit = st.form_submit_button("Send")

# On new question, clear previous state and generate SQL + preview
if question_submit:
    for key in [
        "raw_sql_block", "sql", "is_modifying",
        "preview_sql", "preview_before",
        "result", "preview_after", "final_answer",
        "executed", "confirm"
    ]:
        st.session_state.pop(key, None)

    raw = generate_query.invoke({"question": st.session_state.question_input})
    sql = extract_sql(raw)
    is_modifying = bool(re.match(r'^(INSERT|UPDATE|DELETE)', sql, re.IGNORECASE))

    st.session_state.raw_sql_block = raw
    st.session_state.sql = sql
    st.session_state.is_modifying = is_modifying

    # Build preview SELECT
    preview_sql = None
    if is_modifying:
        kind = sql.split()[0].upper()
        if kind in ("UPDATE", "DELETE"):
            m = re.match(
                r'^(?:UPDATE|DELETE)\s+(\w+)\s+.*WHERE\s+(.+)$',
                sql, re.IGNORECASE | re.DOTALL
            )
            if m:
                table, where = m.group(1), m.group(2)
                preview_sql = f"SELECT * FROM {table} WHERE {where}"
        elif kind == "INSERT":
            m = re.match(r'^INSERT\s+INTO\s+(\w+)', sql, re.IGNORECASE)
            if m:
                table = m.group(1)
                preview_sql = f"SELECT * FROM {table} ORDER BY 1 DESC LIMIT 5"

        st.session_state.preview_sql = preview_sql
        if preview_sql:
            st.session_state.preview_before = execute_query.invoke(preview_sql)

    # If not modifying, execute immediately
    else:
        main_sql = sql.split(";")[0].strip()
        res = execute_query.invoke(main_sql)
        st.session_state.result = res
        st.session_state.final_answer = rephrase_answer.invoke({
            "question": st.session_state.question_input,
            "query": main_sql,
            "result": res
        })
        st.session_state.executed = True

# Step 2: Display raw + proposed SQL
if "sql" in st.session_state:
    st.subheader("Raw AI Output")
    st.code(st.session_state.raw_sql_block)

    st.subheader("Proposed SQL")
    st.code(st.session_state.sql)

    # If modifying: show before-preview + confirm checkbox + execute button
    if st.session_state.is_modifying:
        st.subheader("Preview (Before)")
        st.write(st.session_state.preview_before or "No matching rows")

        st.session_state.confirm = st.checkbox(
            "I understand this will modify the database",
            key="confirm_checkbox"
        )
        execute_now = st.button("Execute Change")

        if st.session_state.confirm and execute_now:
            main_sql = st.session_state.sql.split(";")[0].strip()
            res = execute_query.invoke(main_sql)
            st.session_state.result = res
            # after-preview
            if st.session_state.preview_sql:
                st.session_state.preview_after = execute_query.invoke(
                    st.session_state.preview_sql
                )
            st.session_state.final_answer = rephrase_answer.invoke({
                "question": st.session_state.question_input,
                "query": main_sql,
                "result": res
            })
            st.session_state.executed = True

    # Step 3: Display results + after-preview + answer
    if st.session_state.get("executed", False):
        st.subheader("Raw Result")
        st.write(st.session_state.result)

        if st.session_state.is_modifying and st.session_state.get("preview_after") is not None:
            st.subheader("Preview (After)")
            st.write(st.session_state.preview_after)

        st.subheader("Answer")
        st.write(st.session_state.final_answer)
