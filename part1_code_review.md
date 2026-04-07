# Part 1: Code Review & Debugging

## Issues Identified

### 1. No Input Validation
The code directly accesses fields like `data['name']`, `data['sku']`, etc. without checking if they exist.

**Impact:**  
If the request body is missing any required field (for example, only sending `{"name": "Widget"}`), the API will crash with a KeyError. Instead of a proper client error (400), it returns a 500 server error.

---

### 2. No Error Handling
There are no try-catch blocks around database operations.

**Impact:**  
If something goes wrong (like database failure, invalid input, or duplicate data), the API crashes and returns a generic error. This makes debugging difficult and gives a poor user experience.

---

### 3. Missing SKU Uniqueness Check
The code does not check whether the SKU already exists.

**Impact:**  
Duplicate SKUs can be created, especially if multiple requests come at the same time. This breaks the assumption that SKU is unique and can cause issues in inventory tracking.

---

### 4. Multiple Commits (Data Consistency Issue)
There are two separate `db.session.commit()` calls.

**Impact:**  
If the first commit succeeds (product is created) but the second fails (inventory creation fails), the database ends up in an inconsistent state. The product exists without inventory, which breaks the system logic.

---

### 5. No Proper Handling for Price
Price is stored without validation or conversion.

**Impact:**  
Using float values directly can lead to precision issues (e.g., 10.10 stored as 10.0999). This can affect financial calculations.

---

### 6. Business Logic Issue (Product-Warehouse Relationship)
The product is directly linked to a warehouse, but the requirement states that products can exist in multiple warehouses.

**Impact:**  
This design restricts a product to a single warehouse and does not support real-world inventory scenarios.

---

### 7. Missing Handling for Optional Fields
The code assumes all fields are present.

**Impact:**  
If optional fields like `initial_quantity` are missing, the API may crash.

---

### 8. No Proper HTTP Status Codes
The API always returns 200 OK.

**Impact:**  
Clients cannot differentiate between success and failure, making error handling difficult on the frontend.

---

## Corrected Version

```python
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

@app.route('/api/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'sku', 'price', 'warehouse_id', 'initial_quantity']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing": missing_fields
            }), 400

        # Validate price
        try:
            price = Decimal(str(data['price']))
            if price < 0:
                return jsonify({"error": "Price cannot be negative"}), 400
        except:
            return jsonify({"error": "Invalid price format"}), 400

        # Validate quantity
        try:
            quantity = int(data['initial_quantity'])
            if quantity < 0:
                return jsonify({"error": "Quantity cannot be negative"}), 400
        except:
            return jsonify({"error": "Invalid quantity format"}), 400

        # Check SKU uniqueness
        existing = Product.query.filter_by(sku=data['sku']).first()
        if existing:
            return jsonify({"error": "SKU already exists"}), 409

        # Check warehouse exists
        warehouse = Warehouse.query.get(data['warehouse_id'])
        if not warehouse:
            return jsonify({"error": "Warehouse not found"}), 404

        # Create product (no warehouse_id here)
        product = Product(
            name=data['name'],
            sku=data['sku'],
            price=price
        )

        # Create inventory
        inventory = Inventory(
            product=product,
            warehouse_id=data['warehouse_id'],
            quantity=quantity
        )

        # Single transaction
        db.session.add(product)
        db.session.add(inventory)
        db.session.commit()

        return jsonify({
            "message": "Product created successfully",
            "product_id": product.id
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Database error"}), 409

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
