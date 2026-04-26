from Expense import Expense

class BudgetProfile:
    def __init__(self, monthly_income):
        self.monthly_income = monthly_income
        self.expenses = []

    def add_expense(self, name, mandatory,cost):
        self.expenses.append(Expense(name, mandatory,cost))

    def update_income(self,income):
        self.income = income

    def to_dict(self):
        return {
            "monthly_income": self.monthly_income,
            "expenses": [expense.to_dict() for expense in self.expenses]
        }

    @staticmethod
    def from_dict(data):
        budget = BudgetProfile(data["monthly_income"])

        for expense_data in data["expenses"]:
            budget.expenses.append(Expense.from_dict(expense_data))

        return budget