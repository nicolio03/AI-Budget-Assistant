import json
import os
from User import User

class UserManager:
    def __init__(self, filename = "users.json"):
        self.filename = filename
        self.users = {}
        self.load_users()

    def add_user(self, user):
        if user.username in self.users:
            return False
        self.users[user.username] = user
        self.save_users()
        return True

    def get_user(self, username):
        return self.users.get(username)

    def authenticate(self, username, password):
        user = self.users.get(username)
        if user and user.check_password(password):
            return user
        return None
    
    def save_users(self):
        data = {
            username: user.to_dict()
            for username, user in self.users.items()
        }

        with open(self.filename, "w") as file:
            json.dump(data, file, indent=4)

    def load_users(self):
        if not os.path.exists(self.filename):
            self.users = {}
            return

        with open(self.filename, "r") as file:
            data = json.load(file)

        self.users = {
            username: User.from_dict(user_data)
            for username, user_data in data.items()
        }