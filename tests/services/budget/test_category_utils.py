from backend.app.services.budget.category_utils import is_expense_category


def test_is_expense_category_excludes_income_like_categories() -> None:
    for category in [
        "Salary",
        "Interest",
        "Refund",
        "Cashback",
        "Dividend",
        "Income",
        "Credit",
        "Salary Credit",
    ]:
        assert is_expense_category(category) is False


def test_is_expense_category_includes_regular_expense_categories() -> None:
    for category in [
        "Food",
        "Rent",
        "Fuel",
        "Shopping",
        "Utilities",
        "Credit Card Bills",
    ]:
        assert is_expense_category(category) is True
