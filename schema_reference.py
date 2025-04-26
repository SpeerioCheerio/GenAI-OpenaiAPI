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
