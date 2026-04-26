import ipywidgets as widgets
from IPython.display import display
import webbrowser
from Expense import Expense
from User import User
from UserManager import UserManager
from BudgetProfile import BudgetProfile
from BudgetAgent import BudgetAgent
from pypdf import PdfReader
import io
import re

user_manager = UserManager()
output = widgets.Output()

def start_screen():
    app = widgets.VBox()
    show_start_screen(app)
    display(app)

def normalize_allocations_to_income(user):
    total_allocated = sum(exp.allocation for exp in user.budget.expenses)

    if total_allocated <= 0:
        return

    scale = user.budget.monthly_income / total_allocated

    for expense in user.budget.expenses:
        expense.allocation = round(expense.allocation * scale, 2)

def show_transaction_review_screen(app, user, transactions):
    output = widgets.Output()
    index = {"current": 0}

    # expense options + None
    expense_options = ["None"] + [expense.title for expense in user.budget.expenses]

    pending_lables = {}

    def show_current_transaction():
        if index["current"] >= len(transactions):
            
            user.transactions = transactions

            if not hasattr(user, "learned_labels"):
                user.learned_labels = {}

            user.learned_labels.update(pending_lables)

            actuals, recommendations = update_allocations_from_actual_usage(user)

            user.actual_spending = actuals
            user.recommendations = recommendations

            with output:
                output.clear_output()
                print("All transactions reviewed.")

            show_dashboard(app,user)
            return

        tx = transactions[index["current"]]

        guessed_title = tx.get("assigned_title", "None")
        if guessed_title is None:
            guessed_title = "None"

        if guessed_title not in expense_options:
            guessed_title = "None"

        assign_dropdown = widgets.Dropdown(
            options=expense_options,
            value=guessed_title,
            description="Assign:"
        )

        transaction_text = widgets.HTML(
            value=(
                f"<h3>Review Transaction</h3>"
                f"<b>Transaction {index['current'] + 1} of {len(transactions)}</b><br>"
                f"<b>Description:</b> {tx.get('description', '')}<br>"
                f"<b>Amount:</b> ${tx.get('amount', 0):.2f}"
            )
        )

        back_btn = widgets.Button(description="Back", button_style="warning")
        next_btn = widgets.Button(description="Save / Next", button_style="success")


        def save_current_choice(b):
            selected = assign_dropdown.value

            if selected == "None":
                tx["assigned_title"] = None
                tx["count_in_budget"] = False
            else:
                tx["assigned_title"] = selected
                tx["count_in_budget"] = True

                keyword = tx["description"].upper().split()[0]
                if not hasattr(user, "learned_labels"):
                    user.learned_labels = {}

                keyword = tx["description"].upper().split()[0]
                user.learned_labels[keyword] = selected

        def next_clicked(b):
            save_current_choice(b)
            index["current"] += 1
            show_current_transaction()

        def back_clicked(b):
            save_current_choice(b)

            if index["current"] > 0:
                index["current"] -= 1

            show_current_transaction()

        back_btn.on_click(back_clicked)
        next_btn.on_click(next_clicked)

        app.children = [
            transaction_text,
            assign_dropdown,
            widgets.HBox([back_btn, next_btn]),
            output
        ]

    show_current_transaction()


def parse_transactions_from_text(full_text):
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    transactions = []

    money_re = re.compile(r"^-?\$[\d,]+\.\d{2}$")
    date_re = re.compile(r"^\d{1,2}/\d{1,2}$")

    i = 0

    while i < len(lines) - 2:
        # Pattern:
        # New Balance
        # Balance Change
        # Description lines...
        if money_re.match(lines[i]) and money_re.match(lines[i + 1]):
            new_balance = lines[i]
            amount_text = lines[i + 1]
            amount = float(amount_text.replace("$", "").replace(",", ""))

            desc_lines = []
            j = i + 2

            while j < len(lines):
                # Stop if next transaction starts:
                # money line followed by money line
                if j + 1 < len(lines) and money_re.match(lines[j]) and money_re.match(lines[j + 1]):
                    break

                # Stop on page/footer junk
                if lines[j].startswith("Page "):
                    break
                if lines[j] in ["Transaction History", "Post", "Date", "Transaction Description", "New Balance", "Balance Change"]:
                    j += 1
                    continue

                desc_lines.append(lines[j])
                j += 1

            description = " ".join(desc_lines).strip()

            if description:
                transactions.append({
                    "description": description,
                    "amount": amount,
                    "new_balance": new_balance
                })

            i = j
        else:
            i += 1

    return transactions

def show_start_screen(app):
    user_input = widgets.Text(description="Username:")
    pass_input = widgets.Password(description="Password:")
    create_user_btn = widgets.Button(description="Create User",button_style='')
    sign_in_btn = widgets.Button(description="Sign In",button_style='')

    def sign_in_clicked(b):
        with output:
            output.clear_output()

            username = user_input.value.strip()
            password = pass_input.value
            user = user_manager.authenticate(username, password)

            if user:
                show_dashboard(app,user)
            else:
                print("Invalid credentials")

    def create_user_clicked(b):
        with output:
            output.clear_output() 

            create_user_screens(app)

    sign_in_btn.on_click(sign_in_clicked)
    create_user_btn.on_click(create_user_clicked)

    app.children = [
        widgets.HTML("<h3>Welcome</h3>"),
        user_input,
        pass_input,
        widgets.HBox([sign_in_btn, create_user_btn]),
        output
    ]

def show_expense_screen(app, user):
    #listing all widgets
    expense_input = widgets.Text(description="Expense Title:")
    add_btn = widgets.Button(description="Add",button_style='success')
    done_btn = widgets.Button(description="Done",button_style='info')
    remove_btn = widgets.Button(description="Remove Selected",button_style='danger')
    back_btn = widgets.Button(description="Back",button_style='warning')
    
    summary_html = widgets.HTML()
    expenses_box = widgets.VBox()

    remove_selector = widgets.RadioButtons(options=[],description="Remove:",layout=widgets.Layout(width="max-content"))

    def update_summary(change=None):
        total_allocated = sum(exp.allocation for exp in user.budget.expenses)
        remaining = user.budget.monthly_income - total_allocated

        summary_html.value = (
        f"<b>Monthly Income:</b> ${user.budget.monthly_income:.2f} | "
        f"<b>Allocated:</b> ${total_allocated:.2f} | "
        f"<b>Remaining:</b> ${remaining:.2f}</span>")

    def refresh_expenses():
        rows = []
        radio_options = []

        for i, expense in enumerate(user.budget.expenses):
            title_label = widgets.HTML(value=f"<b>{expense.title}</b>")

            mandatory_dropdown = widgets.Dropdown(
                options=[("Mandatory", True), ("Optional", False)],
                value=expense.mandatory,
                )

            amount_input = widgets.FloatText(
                value=expense.allocation,
                layout=widgets.Layout(width="140px")
            )

            def make_dropdown_handler(exp):
                def changed(change):
                    if change["name"] == "value":
                        exp.mandatory = change["new"]
                return changed

            def make_amount_handler(exp):
                def changed(change):
                    if change["name"] == "value":
                        exp.allocation = change["new"]
                        update_summary()
                return changed

            mandatory_dropdown.observe(
            make_dropdown_handler(expense),
            names="value"
            )

            amount_input.observe(
                make_amount_handler(expense),
                names="value"
            )

            row = widgets.HBox([title_label, mandatory_dropdown,widgets.HTML("<b>Allocated:</b>"), amount_input])
            rows.append(row)

            radio_options.append((expense.title, i))
        
        expenses_box.children = rows
        remove_selector.options = radio_options

        if radio_options:
            remove_selector.value = radio_options[0][1]
        else:
            remove_selector.value = None

        update_summary()

    def add_clicked(b):
        title = expense_input.value.strip()

        if not title:
            with output:
                output.clear_output()
                print("Enter an expense title.")
            return

        user.budget.add_expense(title, False, 0.0)
        expense_input.value = ""
        refresh_expenses()

    def remove_clicked(b):
        selected_index = remove_selector.value

        if selected_index is None:
            with output:
                output.clear_output()
                print("No expense selected.")
            return

        user.budget.expenses.pop(selected_index)
        refresh_expenses()

    def back_clicked(b):
        show_dashboard(app, user)

    def done_clicked(b):
        show_dashboard(app,user)


    add_btn.on_click(add_clicked)
    remove_btn.on_click(remove_clicked)
    back_btn.on_click(back_clicked)
    done_btn.on_click(done_clicked)
    refresh_expenses()

    app.children = [
    widgets.HTML("<h3>Update Expenses</h3>"),
    summary_html,
    widgets.HBox([expense_input, add_btn]),
    widgets.HTML("<b>Expenses:</b>"),
    expenses_box,
    widgets.HTML("<b>Select an expense to remove:</b>"),
    remove_selector,
    widgets.HBox([remove_btn, back_btn, done_btn]),
    output
    ]

def show_upload_screen(app, user):
    statement_upload= widgets.FileUpload(accept='.pdf',multiple=True)
    done_btn = widgets.Button(description="Done",button_style='info')
    back_btn = widgets.Button(description="Back",button_style='warning')

    def back_clicked(b):
        with output:
            output.clear_output()
        
        show_dashboard(app,user)

    def done_clicked(b):
        with output:
            output.clear_output()

            if not statement_upload.value:
                print("Add at least one file.")
                return

            all_text = ""

            for uploaded_file in statement_upload.value:
                file_name = uploaded_file["name"]
                pdf_bytes = uploaded_file["content"]

                reader = PdfReader(io.BytesIO(pdf_bytes))

                file_text = ""

                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        file_text += text + "\n"

                if not file_text.strip():
                    print("No readable text found. This PDF may be scanned/image-based.")
                    continue

                all_text += f"\n--- {file_name} ---\n"
                all_text += file_text

            if not all_text.strip():
                print("No readable text found in any uploaded file.")
                return

            user.statement_text = all_text

            print("Statement uploaded and read successfully.")
            transactions = parse_transactions_from_text(all_text)
            if not transactions:
                print("No transactions found.")
                return

            user.transactions = transactions

            print(f"Found {len(transactions)} transactions.")
            show_transaction_review_screen(app, user,transactions)
                        
    done_btn.on_click(done_clicked)
    back_btn.on_click(back_clicked)

    app.children = [
        widgets.HTML("<b>Upload one or more PDF bank statements:</b>"),
        statement_upload,
        widgets.HBox([back_btn, done_btn]),
        output
    ]


def show_dashboard(app, user):
    output = widgets.Output()

    income_input = widgets.FloatText(
        value=user.budget.monthly_income,
        description="$"
    )

    summary = widgets.HTML()
    expenses_box = widgets.VBox()

    def update_income(change):
        old_income = user.budget.monthly_income
        new_income = change["new"]

        if new_income <= 0:
            return

        user.budget.monthly_income = new_income

        # Step 1: scale allocations proportionally
        if old_income > 0:
            scale = new_income / old_income
            for expense in user.budget.expenses:
                expense.allocation *= scale

        # Step 2: normalize so total == income exactly
        total_allocated = sum(exp.allocation for exp in user.budget.expenses)

        if total_allocated > 0:
            correction = new_income / total_allocated
            for expense in user.budget.expenses:
                expense.allocation = round(expense.allocation * correction, 2)

        normalize_allocations_to_income(user)
        refresh_expenses()
        update_dashboard_summary()

    income_input.observe(update_income, names="value")

    def update_dashboard_summary():
        total_allocated = sum(exp.allocation for exp in user.budget.expenses)
        remaining = user.budget.monthly_income - total_allocated

        summary.value = (
            f"<b>Income:</b> ${user.budget.monthly_income:.2f} | "
            f"<b>Allocated:</b> ${total_allocated:.2f} | "
            f"<b>Remaining:</b> ${remaining:.2f}"
        )

    def refresh_expenses():
        rows = []

        for expense in user.budget.expenses:
            title = widgets.HTML(f"<b>{expense.title}</b>")

            allocated = widgets.HTML(
                f"${expense.allocation:.2f}"
            )

            rows.append(
                widgets.HBox([
                    title,
                    widgets.HTML("<b>Allocated:</b>"),
                    allocated
                ])
            )

        expenses_box.children = rows

    upload_btn = widgets.Button(description="Upload Statements", button_style="info")
    update_btn = widgets.Button(description="Update Expenses", button_style="warning")
    logout_btn = widgets.Button(description="Logout", button_style="danger")

    def upload_clicked(b):
        show_upload_screen(app,user)

    def update_clicked(b):
        show_expense_screen(app,user)

    def logout_clicked(b):
        show_start_screen(app)

    upload_btn.on_click(upload_clicked)
    update_btn.on_click(update_clicked)
    logout_btn.on_click(logout_clicked)

    def update_income(change):
        old_income = user.budget.monthly_income
        new_income = change["new"]

        if old_income <= 0:
            user.budget.monthly_income = new_income
            update_dashboard_summary()
            return

        scale = new_income / old_income

        user.budget.monthly_income = new_income

        for expense in user.budget.expenses:
            expense.allocation = round(expense.allocation * scale, 2)

        refresh_expenses()
        update_dashboard_summary()
        refresh_expenses()

    income_input.observe(update_income, names="value")

    refresh_expenses()

    app.children = [
        widgets.HTML(f"<h3>Welcome, {user.username}</h3>"),
        widgets.HTML("<b>Monthly Income:</b>"),
        income_input,
        summary,
        widgets.HTML("<h4>Expenses</h4>"),
        expenses_box,
        widgets.HBox([upload_btn, update_btn, logout_btn]),
        output
    ]

def create_user_screens(app):
    #declaring outputs
    state = {
        "monthly_income": 0.0,
        "expenses": [],
    }
    output = widgets.Output()
    budget = BudgetProfile(0.0)

    def show_income_screen():
        #listing all widgets
        income_input = widgets.FloatText(description="$")
        next_btn = widgets.Button(description="Next",button_style='success')
        back_btn = widgets.Button(description="Back",button_style='warning')

        income_input.value = state["monthly_income"]

        def next_clicked(b):
            with output:
                output.clear_output()

                state["monthly_income"] = income_input.value

                if state["monthly_income"] <= 0:
                    print("Enter a valid monthly income.")
                    return
                
                budget.update_income(state["monthly_income"])

                show_expense_screen()

        def back_clicked(b):
            with output:
                output.clear_output()
            
                show_start_screen(app)

        #when buttons clicked
        back_btn.on_click(back_clicked)
        next_btn.on_click(next_clicked)

        app.children = [
            widgets.HTML("<b>Approx. Monthly Income:</b>"),
            income_input,
            widgets.HBox([back_btn, next_btn]),
            output
        ]
        
    def show_expense_screen():
        #listing all widgets
        expense_input = widgets.Text(description="Expense Title:")
        add_btn = widgets.Button(description="Add",button_style='success')
        next_btn = widgets.Button(description="Next",button_style='info')
        remove_btn = widgets.Button(description="Remove Selected",button_style='danger')
        back_btn = widgets.Button(description="Back",button_style='warning')
        
        summary_html = widgets.HTML()
        expenses_box = widgets.VBox()

        remove_selector = widgets.RadioButtons(options=[],description="Remove:",layout=widgets.Layout(width="max-content"))

        def update_summary(change=None):
            total_allocated = 0.0

            for expense in state["expenses"]:
                total_allocated += expense.allocation
            
            remaining = state["monthly_income"] - total_allocated

            summary_html.value = (
            f"<b>Monthly Income:</b> ${state['monthly_income']:.2f} | "
            f"<b>Allocated:</b> ${total_allocated:.2f} | "
            f"<b>Remaining:</b> ${remaining:.2f}</span>")

        def refresh_expenses():
            rows = []
            radio_options = []

            for i, expense in enumerate(state["expenses"]):
                title_label = widgets.HTML(value=f"<b>{expense.title}</b>")

                mandatory_dropdown = widgets.Dropdown(
                    options=[("Mandatory", True), ("Optional", False)],
                    value=expense.mandatory,
                    description=""
                )

                amount_input = widgets.FloatText(
                    value=expense.allocation,
                    description="",
                    layout=widgets.Layout(width="140px")
                )

                def make_dropdown_handler(exp):
                    def dropdown_changed(change):
                        if change["name"] == "value":
                            exp.mandatory = change["new"]
                    return dropdown_changed

                def make_amount_handler(exp):
                    def amount_changed(change):
                        if change["name"] == "value":
                            exp.allocation = change["new"]
                            update_summary()
                    return amount_changed

                mandatory_dropdown.observe(
                make_dropdown_handler(expense),
                names="value"
                )

                amount_input.observe(
                    make_amount_handler(expense),
                    names="value"
                )

                row = widgets.HBox([title_label, mandatory_dropdown,widgets.HTML("<b>Amount:</b>"), amount_input])
                rows.append(row)

                radio_options.append((expense.title, i))
            
            expenses_box.children = rows
            remove_selector.options = radio_options

            if radio_options:
                remove_selector.value = radio_options[0][1]
            else:
                remove_selector.value = None

            update_summary()

        def add_clicked(b):
            with output:
                output.clear_output()

                title = expense_input.value.strip()

                if not title:
                    print("Enter an expense title.")
                    return

                state["expenses"].append(Expense(title, False, 0.0))
                expense_input.value = ""
                refresh_expenses()
        
        def remove_clicked(b):
            with output:
                output.clear_output()

                selected_index = remove_selector.value

                if selected_index is None:
                    print("No title selected.")
                    return
                
                state["expenses"].pop(selected_index)
                refresh_expenses()

        def back_clicked(b):
            with output:
                output.clear_output()
            
            show_income_screen()

        def next_clicked(b):
            with output:
                output.clear_output()

                if not state ["expenses"]:
                    print("Add at least one expense.")
                    return

                show_sign_in_screen()
        
        add_btn.on_click(add_clicked)
        remove_btn.on_click(remove_clicked)
        back_btn.on_click(back_clicked)
        next_btn.on_click(next_clicked)

        refresh_expenses()

        app.children =[
            widgets.HTML("<h3>Step 2: Add and Allocate Expenses</h3>"),
            summary_html,
            widgets.HBox([expense_input, add_btn]),
            widgets.HTML("<b>Expenses:</b>"),
            expenses_box,
            widgets.HTML("<b>Select an expense to remove:</b>"),
            remove_selector,
            widgets.HBox([remove_btn, back_btn, next_btn]),
            output
        ]

    def show_sign_in_screen():
        user_input = widgets.Text(description="Username:")
        pass_input = widgets.Password(description="Password:")
        confirm_input = widgets.Password(description="Confirm Password:")
        back_btn = widgets.Button(description="Back",button_style='success')
        done_btn = widgets.Button(description="Done",button_style='info')

        def back_clicked(b):
            with output:
                output.clear_output()
            
            show_expense_screen()

        def done_clicked(b):
            with output:
                output.clear_output()

                if not user_input.value.strip() or not pass_input.value or not confirm_input.value:
                    print("Please fill all values.")
                    return

                if pass_input.value != confirm_input.value:
                    print("Passwords don't match.")
                    return

                for exp in state["expenses"]:
                    budget.add_expense(exp.title,exp.mandatory,exp.allocation)

                user = User(user_input.value.strip(), pass_input.value, budget)
                if not user_manager.add_user(user):
                    print("That username already exists.")
                    return

                print("User created successfully!")
                show_start_screen(app)
                
        back_btn.on_click(back_clicked)
        done_btn.on_click(done_clicked)

        app.children = [
            widgets.HTML("<h3>Step 3: Sign-up</h3>"),
            user_input,
            pass_input,
            confirm_input,
            widgets.HBox([back_btn, done_btn]),
            output
        ]

    show_income_screen()

def update_allocations_from_actual_usage(user, learning_rate=0.25):
    actuals = {}
    recommendations = []

    for tx in user.transactions:
        if not tx.get("count_in_budget"):
            continue

        title = tx.get("assigned_title")

        if title is None:
            continue

        actuals[title] = actuals.get(title, 0.0) + abs(tx["amount"])

    for expense in user.budget.expenses:
        planned = expense.allocation
        actual = actuals.get(expense.title, 0.0)

        difference = actual - planned
        adjustment = difference * learning_rate

        old_allocation = expense.allocation
        expense.allocation = round(max(0, planned + adjustment),2)

        recommendations.append(
            f"{expense.title}: planned ${old_allocation:.2f}, actual ${actual:.2f}, "
            f"adjusted to ${expense.allocation:.2f}"
        )

    total_allocated = sum(exp.allocation for exp in user.budget.expenses)

    if total_allocated > user.budget.monthly_income:
        scale = user.budget.monthly_income / total_allocated

        for expense in user.budget.expenses:
            expense.allocation *= scale

        recommendations.append(
            "Allocations were scaled down because total planned spending exceeded monthly income."
        )

    return actuals, recommendations