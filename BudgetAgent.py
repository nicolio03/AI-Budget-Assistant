import ipywidgets as widgets

class BudgetAgent:
    def __init__(self):
        self.learned_labels = {}

    def predict_title(self, description):
        description_upper = description.upper()

        for keyword, title in self.learned_labels.items():
            if keyword in description_upper:
                return title

        return "Unknown"

    def learn(self, description, selected_title):
        keyword = description.upper().split()[0]
        self.learned_labels[keyword] = selected_title

