# Part 1: Code Review & Debugging

## Issues Identified

### 1. **No Input Validation**
**Problem:** The code directly accesses `data['name']`, `data['sku']`, etc. without checking if they exist.

**What Goes Wrong:** If a client sends incomplete JSON like `{"name": "Widget"}`, the code crashes with a `KeyError`.

**Production Impact:** API returns 500 Internal Server Error instead of helpful 400 Bad Request.

---

### 2. **No Error Handling**
**Problem:** No try-catch blocks around database operations.

**What Goes Wrong:** 
- Database connection fails → unhandled exception
- Duplicate SKU violation → crashes instead of returning helpful error
- Invalid data types → crashes

**Production Impact:** Users see generic errors, and developers can't diagnose issues easily.

---

### 3. **Missing SKU Uniqueness Check**
**Problem:** The code doesn't verify SKU is unique before inserting.

**What Goes Wrong:** Two products with same SKU can be created if they're submitted simultaneously (race condition).

**Production Impact:** Data integrity violation. Business logic assumes SKUs are unique.

---

### 4. **Multiple Commits Create Data Inconsistency**
**Problem:** Two separate `db.session.commit()` calls.

**What Goes Wrong:** 
- First commit succeeds (Product created)
- Second commit fails (Inventory creation fails)
- Result: Product exists without inventory record

**Production Impact:** Orphaned products in database. Inventory tracking broken.

---

### 5. **No Decimal Handling for Price**
**Problem:** Price stored as-is without validation or decimal precision.

**What Goes Wrong:** Float precision errors ($10.10 might store as $10.099999).

**Production Impact:** Financial calculations become inaccurate over time.

---

### 6. **Business Logic Flaw: Product-Warehouse Relationship**
**Problem:** Code creates Product with a single `warehouse_id`, but requirements say "products can exist in multiple warehouses."

**What Goes Wrong:** Product tied to one warehouse. Can't track same product across multiple locations.

**Production Impact:** Violates core business requirement.

---

### 7. **Missing Required Fields Handling**
**Problem:** No handling for optional vs required fields.

**What Goes Wrong:** If `initial_quantity` is optional but missing, code crashes.

---

### 8. **No HTTP Status Codes**
**Problem:** Always returns 200 OK, even on errors.

**What Goes Wrong:** Client can't distinguish success from failure programmatically.

---

## Corrected Version

```python
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        # Step 1: Validate input data
        data = request.get_json()
        
        # Check required fields
        required_fields = ['name', 'sku', 'price', 'warehouse_id', 'initial_quantity']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing": missing_fields
            }), 400
        
        # Step 2: Validate data types and values
        try:
            price = Decimal(str(data['price']))
            if price < 0:
                return jsonify({"error": "Price cannot be negative"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid price format"}), 400
        
        try:
            initial_quantity = int(data['initial_quantity'])
            if initial_quantity < 0:
                return jsonify({"error": "Quantity cannot be negative"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid quantity format"}), 400
        
        # Step 3: Check if SKU already exists
        existing_product = Product.query.filter_by(sku=data['sku']).first()
        if existing_product:
            return jsonify({
                "error": "SKU already exists",
                "existing_product_id": existing_product.id
            }), 409  # Conflict status code
        
        # Step 4: Verify warehouse exists
        warehouse = Warehouse.query.get(data['warehouse_id'])
        if not warehouse:
            return jsonify({"error": "Warehouse not found"}), 404
        
        # Step 5: Create product (without warehouse_id - fixing business logic)
        # Products should NOT be tied to a single warehouse
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price
        )
        
        # Step 6: Create inventory record for this warehouse
        inventory = Inventory(
            product=product,  # Relationship will set product_id after commit
            warehouse_id=data['warehouse_id'],
            quantity=initial_quantity
        )
        
        # Step 7: Add both to session and commit ONCE (atomic transaction)
        db.session.add(product)
        db.session.add(inventory)
        db.session.commit()
        
        # Step 8: Return success with proper status code
        return jsonify({
            "message": "Product created successfully",
            "product_id": product.id,
            "sku": product.sku,
            "initial_inventory": {
                "warehouse_id": inventory.warehouse_id,
                "quantity": inventory.quantity
            }
        }), 201  # Created status code
        
    except IntegrityError as e:
        # Handle database constraint violations
        db.session.rollback()
        return jsonify({
            "error": "Database constraint violation",
            "details": str(e.orig)
        }), 409
    
    except Exception as e:
        # Handle unexpected errors
        db.session.rollback()
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

```

## Key Improvements Explained

### 1. **Input Validation (Lines 7-16)**
- Check all required fields exist before processing
- Return 400 Bad Request with specific missing fields
- Prevents KeyError crashes

### 2. **Data Type Validation (Lines 18-31)**
- Convert price to Decimal for financial accuracy
- Validate quantity is a positive integer
- Return 400 with helpful error messages

### 3. **SKU Uniqueness (Lines 33-38)**
- Query database for existing SKU
- Return 409 Conflict if duplicate found
- Prevents race conditions better than relying only on DB constraint

### 4. **Single Atomic Commit (Lines 50-54)**
- Both Product and Inventory added to session
- ONE commit operation
- If either fails, both roll back (all-or-nothing)

### 5. **Proper Error Handling (Lines 62-73)**
- IntegrityError for constraint violations
- Generic Exception for unexpected errors
- Always rollback on failure
- Return appropriate HTTP status codes

### 6. **Business Logic Fix (Lines 43-49)**
- Removed `warehouse_id` from Product model
- Product can now exist in multiple warehouses
- Inventory record links product to warehouse

### 7. **HTTP Status Codes (Lines 60, 39, etc.)**
- 201: Created (success)
- 400: Bad Request (invalid input)
- 404: Not Found (warehouse doesn't exist)
- 409: Conflict (duplicate SKU)
- 500: Internal Server Error

---

## What I Learned from This Exercise

1. **Always validate user input** - Never trust client data
2. **Use single transactions** - Avoid partial data states
3. **Return meaningful errors** - Help clients debug issues
4. **Think about business logic** - Code must match real-world requirements
5. **Handle edge cases** - Concurrent requests, missing data, etc.
