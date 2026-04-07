-- Part 2: Database Design

-- Companies
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

-- Warehouses
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    name VARCHAR(255) NOT NULL
);

-- Products
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    price DECIMAL(10,2)
);

-- Inventory (important table)
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    warehouse_id INTEGER REFERENCES warehouses(id),
    quantity INTEGER DEFAULT 0,
    UNIQUE(product_id, warehouse_id)
);

-- Suppliers
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    contact_email VARCHAR(255)
);

-- Product-Supplier Mapping
CREATE TABLE product_suppliers (
    product_id INTEGER REFERENCES products(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    PRIMARY KEY(product_id, supplier_id)
);


## Design Explanation

I designed the schema based on the requirement that a product can exist in multiple warehouses.

- The **inventory table** is the key part of the design.
- It connects products and warehouses and stores quantity.
- This allows the same product to be stored in different warehouses.

## Relationships

- One company → multiple warehouses
- One product → multiple warehouses (through inventory)
- One product → multiple suppliers

## Assumptions

- SKU is unique across the system
- Each company has its own warehouses
- Products can have more than one supplier

## Key Design Decision

I separated inventory from the product table because storing quantity directly in product would not support multiple warehouses.

This structure makes the system more scalable and flexible.
