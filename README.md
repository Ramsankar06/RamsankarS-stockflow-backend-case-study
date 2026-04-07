# StockFlow Case Study Solution

**Candidate:** [Your Name]  
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
└── assumptions.md                    # All assumptions made
```

## Part 1: Code Review & Debugging

**File:** `part1_code_review.md`

### Issues Identified (7 total)
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

### Questions for Product Team (10 total)
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

### Edge Cases Handled (10 total)
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

## Key Assumptions

### Part 1 Assumptions
- Products can exist in multiple warehouses (per requirements)
- SKUs must be globally unique
- Price is mandatory, quantity can be zero
- Flask framework with SQLAlchemy ORM

### Part 2 Assumptions
- PostgreSQL database (for generated columns)
- Multi-tenant system (one database, multiple companies)
- Soft deletes not required (using hard deletes with CASCADE)
- UTC timestamps for all dates

### Part 3 Assumptions
- "Recent sales" = last 30 days (configurable)
- Days until stockout = current_stock / avg_daily_sales
- Primary supplier is contact for reordering
- Authentication handled by middleware
- Single database instance (not distributed)

## Technologies Used

- **Language:** Python 3.9+
- **Framework:** Flask
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL
- **Testing:** pytest (for unit tests)

## How to Run (If This Were Real Code)

### Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask sqlalchemy psycopg2-binary

# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/stockflow"
export FLASK_APP=app.py

# Run migrations
flask db upgrade

# Start server
flask run
```

### Test the API
```bash
# Get low-stock alerts for company ID 1
curl http://localhost:5000/api/companies/1/alerts/low-stock

# With query parameters
curl "http://localhost:5000/api/companies/1/alerts/low-stock?days_lookback=60&min_days=5"
```

## What I Learned

### Technical Skills
1. **Atomic transactions** - Critical for data consistency
2. **Database normalization** - Prevents data duplication
3. **Query optimization** - One complex query beats many simple ones
4. **Error handling** - Always validate input and handle exceptions

### Business Understanding
1. **Ask questions** - Requirements are never complete
2. **Think about scale** - Design for growth from day one
3. **Audit trails matter** - Especially in inventory/financial systems
4. **User experience** - APIs should be helpful, not just functional

### Collaboration
1. **Document assumptions** - Makes code reviewable
2. **Explain decisions** - Helps team understand trade-offs
3. **List alternatives** - Shows depth of thinking
4. **Be honest about gaps** - Better to ask than guess

## Future Improvements

If I had more time, I would:
1. Add comprehensive unit tests (pytest)
2. Implement authentication/authorization (JWT)
3. Add API rate limiting
4. Create background job for alert caching
5. Add bundle product logic
6. Implement transfer requests between warehouses
7. Add metrics/monitoring (StatsD, Grafana)
8. Write API documentation (Swagger/OpenAPI)

## Contact

Ready to discuss my solutions in the live session!

- **Email:** [your-email@example.com]
- **GitHub:** [your-github-username]
- **LinkedIn:** [your-linkedin-url]

---

**Time Spent:** 90 minutes  
**Submitted:** April 7, 2026
