from django.urls import path
from .views import *

urlpatterns = [
    # path('dashboard/',dashboarduser)
    path("", home, name="home"),
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("logout/", logout_view, name="logout"),

    path("income-list/", income_list, name="income-list"),
    path("income/add/", add_income, name="add-income"),

    path("expenses/", expense_list, name="expense-list"),
    path("expenses/add/", add_expense, name="expense-add"),

    path("accounts/", account_list, name="account-list"),
    path("accounts/add/", add_account, name="account-add"),

    path("reports/", reports_view, name="report-list"),

    path("settings/", settings_view, name="settings"),

    path('api/financial-analysis/', financial_analysis_api, name='financial-analysis-api'),

]
