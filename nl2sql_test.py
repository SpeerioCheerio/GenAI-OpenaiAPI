import os
import re
from operator import itemgetter

from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_openai import ChatOpenAI
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Configure
#THIS SI THE PLACE WHERE THE OPENAIAPI WOULD GO, HAVE TO TAKE OUT SINCE PUBLIC GITHUB
DB_USER     = "root"
DB_PASSWORD = "Aes2024358.."
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_NAME     = "classicmodels"

# 2. Schema reference to embed into LangChain
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

# 3. Connect with embedded schema info
uri = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
db = SQLDatabase.from_uri(uri, custom_table_info={DB_NAME: schema_reference})

# 4. Init LLM + Tools
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
generate_query = create_sql_query_chain(llm, db)
execute_query = QuerySQLDatabaseTool(db=db)

# 5. Rephrasing prompt template
answer_prompt = PromptTemplate.from_template(
    """Given the following user question, corresponding SQL query, and SQL result, answer the user question in a clear, conversational style.

Question: {question}
SQL Query: {query}
SQL Result: {result}

Answer:"""
)
rephrase_answer = answer_prompt | llm | StrOutputParser()

# 6. Robust SQL extractor
def extract_sql(text: str) -> str:
    # strip code fences
    text = re.sub(r'```[^\n]*\n', '', text).replace('```', '')
    # remove lone “sql” or “SQLQuery” lines
    lines = [
        line for line in text.splitlines()
        if not re.match(r'^\s*(sql|SQLQuery)\s*[:\-]?\s*$', line, re.IGNORECASE)
    ]
    cleaned = "\n".join(lines)
    # find first SQL keyword
    m = re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|WITH)\b', cleaned, re.IGNORECASE)
    sql = cleaned[m.start():] if m else cleaned
    return sql.strip().rstrip(';')

# 7. CLI Loop with confirmation for modifying statements
print("Ask anything (type 'exit' to quit):")
while True:
    q = input(">> ")
    if q.lower() in {"exit", "quit"}:
        break
    try:
        raw = generate_query.invoke({"question": q})
        print("\nRaw GPT-4o output:\n", raw)

        sql = extract_sql(raw)
        print("\nProposed SQL:\n", sql)

        # if it modifies data, ask for confirmation
        if re.match(r'^(INSERT|UPDATE|DELETE|CREATE|DROP)\b', sql, re.IGNORECASE):
            confirm = input("This will modify the database. Proceed? (yes/no): ")
            if confirm.strip().lower() != "yes":
                print("Operation cancelled by user.\n")
                continue

        # execute SQL
        res = execute_query.invoke(sql)
        print("\nRaw Result:\n", res)

        # human-friendly answer
        human_answer = rephrase_answer.invoke({
            "question": q,
            "query": sql,
            "result": res
        })
        print("\nRephrased Answer:\n", human_answer, "\n")

    except Exception as err:
        print("Error:", err, "\n")
