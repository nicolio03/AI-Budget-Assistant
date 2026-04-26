import hashlib
from BudgetProfile import BudgetProfile
from BudgetAgent import BudgetAgent

class User:
    def __init__(self, username, password, budget):
        self.username = username
        self.password_hash = self.hash_password(password)
        self.budget = budget
        self.agent = BudgetAgent()
        self.transactions = []
        self.actual_spending = {}
        self.recommendations = []
        self.learned_labels = {}

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.hash_password(password) == self.password_hash
    
    def to_dict(self):
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "budget": self.budget.to_dict()
        }

    @staticmethod
    def from_dict(data):
        user = User(
        data["username"],
        "",  # placeholder, we will override hash
        BudgetProfile.from_dict(data["budget"])
        )
        user.password_hash = data["password_hash"]
        return user