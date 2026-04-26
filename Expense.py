import ipywidgets as widgets
from IPython.display import display
import webbrowser

class Expense:
    def __init__(self, title, mandatory, allocation=0.0):
        self.title = title
        self.mandatory = mandatory
        self.allocation = allocation

    def to_dict(self):
        return {
            "title": self.title,
            "mandatory": self.mandatory,
            "allocation": self.allocation
        }

    @staticmethod
    def from_dict(data):
        return Expense(
            data["title"],
            data["mandatory"],
            data["allocation"]
        )