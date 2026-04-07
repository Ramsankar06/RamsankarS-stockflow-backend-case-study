# Part 3: Low-Stock Alerts API Implementation

## Implementation (Python/Flask with SQLAlchemy)

```python
from flask import Blueprint, jsonify, request
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from decimal import Decimal

api = Blueprint('api', __name__)

@api.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts(company_id):
    """
    Get low-stock alerts for a company across all warehouses.
    
    Business Rules:
    - Only alert for products with sales in the last 30 days
    - Compare current stock to product-specific threshold
    - Calculate days until stockout based on average daily sales
    - Include primary supplier information for reordering
    """
    
    try:
        # Step 1: Verify company exists
        company = Company.query.get(company_id)
        if not company:
            return jsonify({"error": "Company not found"}), 404
        
        # Step 2: Get optional query parameters
        days_lookback = request.args.get('days_lookback', 30, type=int)  # Default 30 days
        min_days_until_stockout = request.args.get('min_days', 0, type=int)  # Filter by urgency
        
        # Validate parameters
        if days_lookback < 1 or days_lookback > 365:
            return jsonify({"error": "days_lookback must be between 1 and 365"}), 400
        
        # Step 3: Calculate date threshold for "recent sales"
        sales_cutoff_date = datetime.now().date() - timedelta(days=days_lookback)
        
        # Step 4: Build complex query to find low-stock products
        # This query does multiple things:
        # - Joins inventory with products and warehouses
        # - Calculates total sales in the lookback period
        # - Filters for products below threshold
        # - Gets primary supplier information
        
        subquery = db.session.query(
            Sales.product_id,
            Sales.warehouse_id,
            func.sum(Sales.quantity_sold).label('total_sold'),
            func.count(Sales.id).label('sale_count')
        ).filter(
            Sales.sale_date >= sales_cutoff_date
        ).group_by(
            Sales.product_id,
            Sales.warehouse_id
        ).subquery()
        
        # Main query
        alerts_query = db.session.query(
            Product.id.label('product_id'),
            Product.name.label('product_name'),
            Product.sku,
            Product.low_stock_threshold.label('threshold'),
            Warehouse.id.label('warehouse_id'),
            Warehouse.name.label('warehouse_name'),
            Inventory.available_quantity.label('current_stock'),
            subquery.c.total_sold,
            subquery.c.sale_count,
            Supplier.id.label('supplier_id'),
            Supplier.name.label('supplier_name'),
            Supplier.contact_email.label('supplier_email'),
            ProductSupplier.lead_time_days
        ).select_from(Inventory).join(
            Product, Inventory.product_id == Product.id
        ).join(
            Warehouse, Inventory.warehouse_id == Warehouse.id
        ).outerjoin(
            subquery,
            and_(
                subquery.c.product_id == Product.id,
                subquery.c.warehouse_id == Warehouse.id
            )
        ).outerjoin(
            ProductSupplier,
            and_(
                ProductSupplier.product_id == Product.id,
                ProductSupplier.is_primary == True
            )
        ).outerjoin(
            Supplier, ProductSupplier.supplier_id == Supplier.id
        ).filter(
            Warehouse.company_id == company_id,
            Product.is_active == True,
            # Only alert if stock is below threshold
            Inventory.available_quantity < Product.low_stock_threshold,
            # Only include products with recent sales
            subquery.c.total_sold > 0
        )
        
        # Step 5: Execute query and process results
        results = alerts_query.all()
        
        alerts = []
        for row in results:
            # Calculate average daily sales
            avg_daily_sales = row.total_sold / days_lookback
            
            # Calculate days until stockout
            # Formula: current_stock / average_daily_sales
            if avg_daily_sales > 0:
                days_until_stockout = int(row.current_stock / avg_daily_sales)
            else:
                days_until_stockout = None  # No recent sales velocity
            
            # Apply minimum days filter if specified
            if min_days_until_stockout > 0:
                if days_until_stockout is None or days_until_stockout > min_days_until_stockout:
                    continue  # Skip this alert
            
            # Build alert object
            alert = {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "sku": row.sku,
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "current_stock": row.current_stock,
                "threshold": row.threshold,
                "days_until_stockout": days_until_stockout,
                "recent_sales": {
                    "total_sold": int(row.total_sold),
                    "days_analyzed": days_lookback,
                    "avg_daily_sales": round(avg_daily_sales, 2)
                }
            }
            
            # Add supplier info if available
            if row.supplier_id:
                alert["supplier"] = {
                    "id": row.supplier_id,
                    "name": row.supplier_name,
                    "contact_email": row.supplier_email,
                    "lead_time_days": row.lead_time_days
                }
            else:
                alert["supplier"] = None
                alert["warning"] = "No primary supplier configured"
            
            alerts.append(alert)
        
        # Step 6: Sort alerts by urgency (lowest days_until_stockout first)
        # Put None values (no velocity) at the end
        alerts.sort(key=lambda x: (
            x['days_until_stockout'] is None,  # None values go last
            x['days_until_stockout'] if x['days_until_stockout'] is not None else float('inf')
        ))
        
        # Step 7: Return response
        return jsonify({
            "alerts": alerts,
            "total_alerts": len(alerts),
            "company_id": company_id,
            "generated_at": datetime.now().isoformat(),
            "parameters": {
                "days_lookback": days_lookback,
                "min_days_until_stockout": min_days_until_stockout
            }
        }), 200
    
    except Exception as e:
        # Log error for debugging
        app.logger.error(f"Error generating low-stock alerts: {str(e)}")
        return jsonify({
            "error": "Failed to generate alerts",
            "message": str(e)
        }), 500


# Helper endpoint to get detailed product info from an alert
@api.route('/api/products/<int:product_id>/reorder-info', methods=['GET'])
def get_reorder_info(product_id):
    """
    Get detailed reorder information for a specific product.
    Useful when acting on a low-stock alert.
    """
    
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        # Get all suppliers for this product
        suppliers = db.session.query(
            Supplier,
            ProductSupplier
        ).join(
            ProductSupplier, Supplier.id == ProductSupplier.supplier_id
        ).filter(
            ProductSupplier.product_id == product_id,
            Supplier.is_active == True
        ).all()
        
        supplier_list = []
        for supplier, ps in suppliers:
            supplier_list.append({
                "id": supplier.id,
                "name": supplier.name,
                "contact_email": supplier.contact_email,
                "contact_phone": supplier.contact_phone,
                "is_primary": ps.is_primary,
                "lead_time_days": ps.lead_time_days,
                "minimum_order_quantity": ps.minimum_order_quantity,
                "unit_cost": float(ps.unit_cost) if ps.unit_cost else None
            })
        
        return jsonify({
            "product_id": product.id,
            "name": product.name,
            "sku": product.sku,
            "current_price": float(product.price),
            "suppliers": supplier_list
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

---

## Edge Cases Handled

### 1. **Products with No Recent Sales**
**Scenario:** Product has low stock but no sales in the lookback period.
**Handling:** Excluded from alerts (filter: `subquery.c.total_sold > 0`).
**Reasoning:** No point alerting about dead stock. But we could add a separate "dead stock" report.

### 2. **Products with Zero Sales Velocity**
**Scenario:** Product had sales but avg_daily_sales rounds to 0.
**Handling:** `days_until_stockout = None`, sorted to end of alert list.
**Reasoning:** Can't calculate meaningful stockout date.

### 3. **Multiple Warehouses for Same Product**
**Scenario:** Product X has low stock in Warehouse A but high stock in Warehouse B.
**Handling:** Separate alert for each warehouse. User decides if they want to transfer stock.
**Reasoning:** Each warehouse operates semi-independently.

### 4. **Products with No Supplier**
**Scenario:** Product was created but no supplier assigned.
**Handling:** Alert still generated but `supplier: null` with warning message.
**Reasoning:** Still important to know stock is low, even if reordering path unclear.

### 5. **Concurrent API Calls**
**Scenario:** Two users hit this endpoint simultaneously.
**Handling:** Each gets their own database session, no locking needed (read-only query).
**Reasoning:** Read operations don't modify data, safe to run concurrently.

### 6. **Very High Sales Volume (Integer Overflow)**
**Scenario:** Product sells millions of units per day.
**Handling:** Using INTEGER type (4 bytes) supports up to 2.1 billion.
**Reasoning:** If needed, upgrade to BIGINT. Add monitoring for this.

### 7. **Decimal Precision for Sales Velocity**
**Scenario:** Product sells 1 unit every 3 days (0.333... per day).
**Handling:** Using `round(avg_daily_sales, 2)` for display, but keeping full precision for calculation.
**Reasoning:** Accurate "days until stockout" more important than pretty numbers.

### 8. **Time Zone Issues**
**Scenario:** Company operates across multiple time zones.
**Handling:** Using `datetime.now()` (server time) and date-only comparisons for sales.
**Improvement needed:** Store timezone in company table, convert accordingly.

### 9. **Bundle Products**
**Scenario:** Product is a bundle containing other products.
**Handling:** Current implementation treats bundles like regular products.
**Improvement needed:** Calculate bundle availability based on component availability.

### 10. **Reserved Inventory (Pending Orders)**
**Scenario:** Stock shows 50 units, but 30 are reserved for pending orders.
**Handling:** Using `available_quantity` (generated column = quantity - reserved_quantity).
**Reasoning:** Only alert on truly available stock.

---

## Assumptions Documented

### Database Schema Assumptions
1. `sales` table exists with columns: product_id, warehouse_id, quantity_sold, sale_date
2. `Product` has a `low_stock_threshold` column (INTEGER)
3. `ProductSupplier` has an `is_primary` boolean to identify main supplier
4. `Inventory` has an `available_quantity` computed column

### Business Logic Assumptions
1. **"Recent sales activity" = last 30 days** (configurable via query param)
2. **Days until stockout** = current_stock / average_daily_sales
3. **Primary supplier** is the one to contact for reordering
4. **Only active products** generate alerts (`is_active = TRUE`)
5. **Alerts are per warehouse**, not aggregated at product level

### Technical Assumptions
1. Using PostgreSQL (for generated columns and query syntax)
2. Flask-SQLAlchemy for ORM
3. Single database (not distributed/sharded)
4. API returns JSON
5. Authentication/authorization handled by middleware (not shown)

---

## How to Test This Code

### 1. **Unit Tests** (Example)
```python
def test_low_stock_alerts_basic():
    # Setup: Create company, warehouse, product with low stock
    company = Company(name="Test Corp")
    warehouse = Warehouse(company=company, name="Warehouse 1")
    product = Product(
        company=company,
        sku="TEST-001",
        name="Test Widget",
        price=10.00,
        low_stock_threshold=20
    )
    inventory = Inventory(
        product=product,
        warehouse=warehouse,
        quantity=5,  # Below threshold
        reserved_quantity=0
    )
    
    # Add sales in last 30 days
    for i in range(10):
        sale = Sales(
            product=product,
            warehouse=warehouse,
            quantity_sold=2,
            sale_date=datetime.now().date() - timedelta(days=i)
        )
        db.session.add(sale)
    
    db.session.commit()
    
    # Test: Call API
    response = client.get(f'/api/companies/{company.id}/alerts/low-stock')
    
    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data['total_alerts'] == 1
    assert data['alerts'][0]['product_id'] == product.id
    assert data['alerts'][0]['current_stock'] == 5
```

### 2. **Integration Tests**
- Test with real database
- Verify SQL query performance with large datasets
- Test edge cases (no sales, no supplier, etc.)

### 3. **Load Testing**
- Simulate 100 concurrent requests
- Measure response time
- Check for database connection pool exhaustion

---

## Performance Optimizations

### Current Implementation
- Single complex query (better than multiple queries)
- Uses indexes on `sales.sale_date`, `sales.product_id`, `inventory.product_id`
- Filters in SQL (not in Python), reducing data transfer

### Further Optimizations (if needed)
1. **Materialized View**: Pre-calculate alerts daily
2. **Query Result Caching**: Cache results for 5 minutes (use Redis)
3. **Pagination**: Return first 50 alerts, use `?page=2` for more
4. **Database Indexing**: Composite index on `(product_id, warehouse_id, sale_date)`

---

## What I Learned

1. **SQL is powerful** - One query beats multiple round trips
2. **Edge cases matter** - Real-world data is messy
3. **Performance vs. accuracy** - Sometimes approximate is good enough
4. **Document assumptions** - Helps future developers (including future me)
5. **Test early** - Write tests alongside code, not after
