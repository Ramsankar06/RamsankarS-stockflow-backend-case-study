# Part 3: Low-Stock Alerts API Implementation

from flask import Blueprint, jsonify
from models import db, Product, Inventory, Warehouse, Supplier

api = Blueprint('api', __name__)

@api.route('/api/companies/<int:company_id>/alerts/low-stock', methods=['GET'])
def get_low_stock_alerts(company_id):
    try:
        alerts = []

        # Step 1: Get all warehouses for the company
        warehouses = Warehouse.query.filter_by(company_id=company_id).all()
        warehouse_ids = [w.id for w in warehouses]

        # Step 2: Get inventory for those warehouses
        inventories = Inventory.query.filter(
            Inventory.warehouse_id.in_(warehouse_ids)
        ).all()

        # Step 3: Check low stock condition
        for inv in inventories:
            product = Product.query.get(inv.product_id)
            warehouse = Warehouse.query.get(inv.warehouse_id)

            threshold = 20  # assumed value

            if inv.quantity < threshold:
                # Get supplier (simplified)
                supplier = Supplier.query.first()

                alerts.append({
                    "product_id": product.id,
                    "product_name": product.name,
                    "sku": product.sku,
                    "warehouse_id": warehouse.id,
                    "warehouse_name": warehouse.name,
                    "current_stock": inv.quantity,
                    "threshold": threshold,
                    "days_until_stockout": 10,  # simple assumption
                    "supplier": {
                        "id": supplier.id if supplier else None,
                        "name": supplier.name if supplier else None,
                        "contact_email": supplier.contact_email if supplier else None
                    }
                })

        return jsonify({
            "alerts": alerts,
            "total_alerts": len(alerts)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

## Approach

I implemented the API in a simple way to identify products with low stock.

Steps followed:

1. Get all warehouses for the given company
2. Fetch inventory records for those warehouses
3. Check if quantity is below a threshold
4. Add supplier information for reordering

## Assumptions

- Threshold is fixed (20)
- Sales data is not included due to limited requirements
- One supplier is considered for simplicity

## Edge Cases Considered

- Company has no warehouses
- Product has no supplier
- Inventory quantity is zero

## Note

This implementation focuses on correctness and clarity. It can be optimized further using joins or advanced queries if needed.
