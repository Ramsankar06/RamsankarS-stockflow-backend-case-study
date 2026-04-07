# StockFlow Case Study Solution

**Candidate:** Ramsankar S
**Position:** Backend Engineering Intern  
**Date:** April 7, 2026

## Overview

This repository contains my solutions for the StockFlow B2B Inventory Management System case study. The case study evaluated my ability to:
- Debug and improve existing code
- Design scalable database schemas
- Implement complex API endpoints
- Work with incomplete requirements

## Repository Structure

```
├── README.md                          # This file
├── part1_code_review.md              # Code review, issues, and fixes
├── part2_database_design.sql         # Database schema design
├── part3_api_implementation.py       # Low-stock alerts API
```

## Part 1: Code Review & Debugging

**File:** `part1_code_review.md`

### Issues Identified
1. No input validation
2. No error handling
3. Missing SKU uniqueness check
4. Multiple commits causing data inconsistency
5. No decimal handling for price
6. Business logic flaw (product tied to single warehouse)
7. Missing HTTP status codes

### Key Fix
Changed from two separate commits to a single atomic transaction, preventing orphaned products.

**Before:**
```python
db.session.add(product)
db.session.commit()  # First commit
db.session.add(inventory)
db.session.commit()  # Second commit - could fail!
```

**After:**
```python
db.session.add(product)
db.session.add(inventory)
db.session.commit()  # Single atomic transaction
```


## Part 2: Database Design

**File:** `part2_database_design.sql`

### Tables Designed (10 total)
- `companies` - Multi-tenant support
- `warehouses` - Multiple locations per company
- `products` - Items being tracked
- `inventory` - Product quantities per warehouse
- `inventory_changes` - Audit trail
- `suppliers` - Vendor management
- `product_suppliers` - Many-to-many linking
- `bundle_components` - Product bundles
- `sales` - Sales history for velocity calculation

### Key Design Decisions
1. **Separate inventory table** - Supports products in multiple warehouses
2. **Audit trail** - `inventory_changes` for regulatory compliance
3. **DECIMAL for money** - Prevents floating-point errors
4. **Generated column** - `available_quantity = quantity - reserved_quantity`
5. **Indexes on foreign keys** - Optimizes common joins

### Questions for Product Team 
Identified missing requirements around user management, product variations, multi-currency support, and more.


## Part 3: API Implementation

**File:** `part3_api_implementation.py`

### Endpoint Implemented
```
GET /api/companies/{company_id}/alerts/low-stock
```

### Business Rules Applied
- Only alert for products with sales in last 30 days
- Calculate days until stockout based on average daily sales
- Include primary supplier for reordering
- Sort by urgency (lowest days remaining first)

### Edge Cases Handled 
- Products with no recent sales
- Products with zero sales velocity
- Multiple warehouses per product
- Products with no supplier
- Time zone considerations
- Reserved inventory (pending orders)

### Query Optimization
- Single complex SQL query instead of multiple round trips
- Uses database indexes effectively
- Filters in SQL, not Python

**Submitted:** April 7, 2026
