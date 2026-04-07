# StockFlow Case Study Solution

**Candidate:** Ramsankar S  
**Position:** Backend Engineering Intern  
**Date:** April 7, 2026  

---

## Overview

This repository contains my solution for the StockFlow B2B Inventory Management System case study.

I approached this problem by first understanding the business requirements and then implementing simple and reliable backend solutions. My focus was on data consistency, proper validation, and keeping the design easy to understand.

---

## Repository Structure
├── README.md
├── part1_code_review.md
├── part2_database_design.sql
├── part3_api_implementation.py


---

## Part 1: Code Review & Debugging

**File:** `part1_code_review.md`

### Issues Identified

- No input validation  
- No error handling  
- Missing SKU uniqueness check  
- Multiple commits causing data inconsistency  
- Price not properly handled  
- Incorrect product-warehouse relationship  
- Missing HTTP status codes  

### Explanation

The original API could fail in multiple ways, especially due to missing validation and the use of multiple database commits.

The most critical issue was data inconsistency. If the product was created successfully but inventory creation failed, the system would end up with incomplete data.

### Key Fix

I solved this by:

- Adding input validation  
- Ensuring SKU uniqueness  
- Adding proper error handling  
- Using a **single transaction** so both product and inventory are created together  

---

## Part 2: Database Design

**File:** `part2_database_design.sql`

### Tables Used

- `companies`
- `warehouses`
- `products`
- `inventory`
- `suppliers`
- `product_suppliers`

### Explanation

The main challenge was supporting products across multiple warehouses.

To solve this, I used a separate **inventory table** that connects products and warehouses and stores quantity.

### Key Design Decisions

- Inventory table handles product-warehouse relationship  
- SKU is kept unique to avoid duplicates  
- Simple schema to keep it scalable and easy to maintain  

### Missing Requirements

Some requirements were not clearly defined, so I would clarify:

- How is low-stock threshold defined?  
- What is considered “recent sales”?  
- Can a product exist without a supplier?  

---

## Part 3: API Implementation

**File:** `part3_api_implementation.py`

### Endpoint
GET /api/companies/{company_id}/alerts/low-stock


### Approach

1. Fetch all warehouses for the company  
2. Get inventory for those warehouses  
3. Check if stock is below a threshold  
4. Include supplier information for reordering  

### Assumptions

- Threshold is fixed for simplicity  
- Sales data is not included  
- One supplier is used per product  

### Edge Cases Considered

- Company has no warehouses  
- Product has no supplier  
- Inventory quantity is zero  

---

## Conclusion

This case study helped me apply backend concepts like validation, database design, and API development in a practical scenario.

I focused on building a clean and understandable solution rather than overcomplicating it, while still ensuring it meets the given requirements.

---

**Submitted:** April 7, 2026
