# StockFlow Case Study Solution

**Candidate:** Ramsankar S  
**Position:** Backend Engineering Intern  
**Date:** April 7, 2026  

---

## Overview

This repository contains my solution for the StockFlow B2B Inventory Management System case study.

I approached this problem by first understanding the business requirements and then implementing simple and correct backend solutions. My focus was on data consistency, proper validation, and clear API design.

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

### Key Fix

The main issue was using multiple commits. I fixed this by using a single transaction so that both product and inventory are created together.

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

### Key Design Decisions

- Used a separate **inventory table** to support products in multiple warehouses  
- Kept SKU unique to avoid duplicate products  
- Used simple relationships to keep the design clean and scalable  

---

## Part 3: API Implementation

**File:** `part3_api_implementation.py`

### Approach

- Fetch all warehouses for a company  
- Get inventory for those warehouses  
- Identify products where stock is below a threshold  
- Include supplier information for reordering  

### Assumptions

- Threshold is fixed (for simplicity)  
- Sales data is not included due to limited requirements  
- One supplier is used per product  

---

## Conclusion

I focused on building a clean and understandable solution by applying backend concepts I am familiar with (from Spring Boot) into Flask. 

Instead of overcomplicating the design, I prioritized correctness, clarity, and alignment with the given requirements.

---

**Submitted:** April 7, 2026

### Endpoint
