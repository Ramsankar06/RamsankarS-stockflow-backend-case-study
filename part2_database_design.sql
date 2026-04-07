# Part 2: Database Design

## Database Schema

### Tables and Relationships

```sql
-- Companies Table
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Warehouses Table
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure warehouse names are unique within a company
    CONSTRAINT unique_warehouse_per_company UNIQUE(company_id, name)
);

CREATE INDEX idx_warehouses_company ON warehouses(company_id);

-- Products Table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) NOT NULL UNIQUE,  -- SKU must be globally unique
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,  -- Using DECIMAL for financial data
    cost DECIMAL(10, 2),  -- Cost from supplier
    product_type VARCHAR(50),  -- 'simple', 'bundle', etc.
    low_stock_threshold INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT positive_price CHECK (price >= 0),
    CONSTRAINT positive_cost CHECK (cost >= 0)
);

CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_products_type ON products(product_type);

-- Inventory Table (tracks product quantities in warehouses)
CREATE TABLE inventory (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,  -- Quantity in pending orders
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    last_counted_at TIMESTAMP,  -- Last physical inventory count
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- One inventory record per product per warehouse
    CONSTRAINT unique_product_warehouse UNIQUE(product_id, warehouse_id),
    CONSTRAINT non_negative_quantity CHECK (quantity >= 0),
    CONSTRAINT non_negative_reserved CHECK (reserved_quantity >= 0)
);

CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_inventory_low_stock ON inventory(available_quantity) WHERE available_quantity > 0;

-- Inventory Changes (audit trail for stock movements)
CREATE TABLE inventory_changes (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER NOT NULL REFERENCES inventory(id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL,  -- 'purchase', 'sale', 'adjustment', 'transfer', 'return'
    quantity_change INTEGER NOT NULL,  -- Positive for additions, negative for reductions
    quantity_before INTEGER NOT NULL,
    quantity_after INTEGER NOT NULL,
    reference_id INTEGER,  -- ID of related order, transfer, etc.
    reference_type VARCHAR(50),  -- 'order', 'transfer', 'adjustment'
    notes TEXT,
    created_by INTEGER,  -- User who made the change
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inv_changes_inventory ON inventory_changes(inventory_id);
CREATE INDEX idx_inv_changes_created_at ON inventory_changes(created_at);
CREATE INDEX idx_inv_changes_type ON inventory_changes(change_type);

-- Suppliers Table
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    address TEXT,
    payment_terms VARCHAR(100),  -- 'Net 30', 'Net 60', etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_suppliers_company ON suppliers(company_id);

-- Product Suppliers (many-to-many: products can have multiple suppliers)
CREATE TABLE product_suppliers (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    supplier_sku VARCHAR(100),  -- Supplier's SKU for this product
    lead_time_days INTEGER,  -- How long it takes to get this product
    minimum_order_quantity INTEGER DEFAULT 1,
    unit_cost DECIMAL(10, 2),  -- Cost per unit from this supplier
    is_primary BOOLEAN DEFAULT FALSE,  -- Is this the primary supplier?
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- One record per product-supplier combination
    CONSTRAINT unique_product_supplier UNIQUE(product_id, supplier_id)
);

CREATE INDEX idx_product_suppliers_product ON product_suppliers(product_id);
CREATE INDEX idx_product_suppliers_supplier ON product_suppliers(supplier_id);

-- Bundle Components (for bundle products containing other products)
CREATE TABLE bundle_components (
    id SERIAL PRIMARY KEY,
    bundle_product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    component_product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,  -- How many of this component in the bundle
    
    -- Prevent product from being its own component
    CONSTRAINT no_self_reference CHECK (bundle_product_id != component_product_id),
    -- One record per bundle-component pair
    CONSTRAINT unique_bundle_component UNIQUE(bundle_product_id, component_product_id)
);

CREATE INDEX idx_bundle_components_bundle ON bundle_components(bundle_product_id);
CREATE INDEX idx_bundle_components_component ON bundle_components(component_product_id);

-- Sales Records (to track sales activity for low-stock alerts)
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id),
    warehouse_id INTEGER NOT NULL REFERENCES warehouses(id),
    quantity_sold INTEGER NOT NULL,
    sale_date DATE NOT NULL,
    total_amount DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_sales_warehouse ON sales(warehouse_id);
```

---

## Entity Relationship Diagram (Text Format)

```
companies (1) ----< (*) warehouses
companies (1) ----< (*) products
companies (1) ----< (*) suppliers

products (*) >----< (*) warehouses  [through inventory]
products (*) >----< (*) suppliers   [through product_suppliers]
products (1) ----< (*) bundle_components (as bundle)
products (1) ----< (*) bundle_components (as component)

inventory (1) ----< (*) inventory_changes
products (1) ----< (*) sales
warehouses (1) ----< (*) sales
```

---

## Design Decisions & Justifications

### 1. **SERIAL PRIMARY KEY**
**Why:** Auto-incrementing integers are simple, fast, and work well for internal IDs.
**Alternative considered:** UUIDs - better for distributed systems, but slower and larger.

### 2. **DECIMAL for Money**
**Why:** Financial precision. DECIMAL(10, 2) stores exactly 2 decimal places, no floating-point errors.
**Alternative considered:** Storing cents as INTEGER - works but less readable.

### 3. **Separate inventory Table**
**Why:** Many-to-many relationship. Same product can exist in multiple warehouses with different quantities.
**Alternative considered:** Storing quantity directly on products - doesn't support multiple warehouses.

### 4. **inventory_changes Audit Trail**
**Why:** 
- Regulatory compliance (track all stock movements)
- Debugging (find why stock levels changed)
- Business intelligence (analyze stock patterns)

### 5. **Indexes on Foreign Keys**
**Why:** Common join operations. `idx_inventory_product` speeds up "show all warehouses with this product."
**Trade-off:** Slower writes, faster reads. Acceptable for inventory systems (more reads than writes).

### 6. **CHECK Constraints**
**Why:** Data integrity at database level. Prevents negative prices/quantities even if application code has bugs.

### 7. **ON DELETE CASCADE**
**Why:** When a company is deleted, all their warehouses, products, etc. should be deleted too.
**Trade-off:** Dangerous if accidentally triggered. Consider soft deletes in production.

### 8. **UNIQUE Constraints**
- `products.sku`: SKUs must be globally unique (business requirement)
- `inventory(product_id, warehouse_id)`: One inventory record per product-warehouse pair
- `product_suppliers(product_id, supplier_id)`: Prevent duplicate supplier entries

### 9. **Generated Column (available_quantity)**
**Why:** Automatically calculates available stock (quantity - reserved). Always consistent.
**Alternative considered:** Calculate in application - risk of inconsistency.

### 10. **Timestamps (created_at, updated_at)**
**Why:** Essential for debugging, auditing, and understanding data lifecycle.

### 11. **Separate sales Table**
**Why:** Needed for "recent sales activity" calculation. Could be replaced by aggregating from orders table if it exists.

---
