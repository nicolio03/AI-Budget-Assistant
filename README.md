# AI Budget Assistant

## Overview
The AI Budget Assistant is a Python-based application that helps users manage their finances by combining user-defined budgeting with transaction analysis from bank statements.

Users can define expenses, upload bank statements, review transactions, and automatically adjust their budget based on actual spending behavior.

---

## Features

- Create and manage a monthly budget  
- Upload PDF bank statements  
- Automatically extract and display transactions  
- Review and categorize transactions one at a time  
- Learn from user corrections to improve future predictions  
- Adjust budget allocations based on real spending  
- Maintain a zero-based budget (no unallocated income)  
- Dynamically update allocations when income changes  

---

## Technologies Used

- Python  
- ipywidgets (UI)  
- pypdf (PDF parsing)  
- JSON (data storage)  

---

## Project Structure
Screen.py # UI and application flow
BudgetAgent.py # AI learning logic
BudgetProfile.py # Budget data model
Expense.py # Expense model
User.py # User model
UserManager.py # Authentication and storage

---

## How It Works

1. User creates a budget with income and expense categories  
2. User uploads a bank statement  
3. Transactions are extracted and displayed  
4. User assigns categories to each transaction  
5. The system learns from these assignments  
6. Budget allocations are adjusted based on actual usage  

---

## Setup

### Clone the repository
git clone https://github.com/nicolio03/AI-Budget-Assistant.git

cd AI-Budget-Assistant

### Install dependencies
pip install ipywidgets pypdf

### Run the application
```python
from Screen import show_start_screen
import ipywidgets as widgets

app = widgets.VBox()
show_start_screen(app)
app
