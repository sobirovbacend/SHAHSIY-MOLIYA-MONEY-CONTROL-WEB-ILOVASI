from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.db import transaction



# def dashboarduser(request):
#     return render(request,"dashboarduser.html")


def home(request):
    return render(request,"home.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Username yoki parol xato")

    return render(request, "login.html")

# @login_required(login_url="login")
# def dashboard_view(request):
#     return render(request, "dashboard.html")

from django.contrib.auth.decorators import login_required
from django.db.models import Sum

# Kelajakda  real API bilan almashtirishim  mumkin.
CURRENCY_RATES = {
    'UZS': 1,
    'USD': 12500,
    'EUR': 13500,
}

# USD -> 100 * 12500 = 1,250,000
# EUR -> 50 * 13500 = 675,000
# UZS -> 2,000,000
# ---------------------
# Jami kirim = 3,925,000 UZS


from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.shortcuts import render
import json


@login_required
def dashboard_view(request):
    user = request.user

    # ======================
    # 1. HISOBLAR
    # ======================
    accounts = Account.objects.filter(user=user, is_active=True)
    incomes = Income.objects.filter(user=user)
    expenses = Expense.objects.filter(user=user)

    # ======================
    # 2. OYLIGI KIRIM-CHIQIMLAR (oy boshidan hozirgacha)
    # ======================
    today = now().date()
    start_month = today.replace(day=1)

    incomes_this_month = incomes.filter(date__gte=start_month)
    expenses_this_month = expenses.filter(date__gte=start_month)

    # ======================
    # 3. JAMI KIRIM, CHIQIM VA UMUMIY BALANS
    # ======================
    total_income_uzs = sum(
        float(inc.amount) * CURRENCY_RATES.get(inc.currency.upper(), 1)
        for inc in incomes_this_month
    )
    total_expense_uzs = sum(
        float(exp.amount) * CURRENCY_RATES.get(exp.currency.upper(), 1)
        for exp in expenses_this_month
    )
    total_balance_uzs = total_income_uzs - total_expense_uzs

    # ======================
    # 4. Formatlash mingliklar bilan
    # ======================
    total_income_uzs_fmt = f"{total_income_uzs:,.0f}"      # 1,250,000
    total_expense_uzs_fmt = f"{total_expense_uzs:,.0f}"    # 675,000
    total_balance_uzs_fmt = f"{total_balance_uzs:,.0f}"    # 575,000

    # ======================
    # 5. Dinamik tahlil (chart uchun)
    # ======================
    chart_data = defaultdict(lambda: {'income': 0, 'expense': 0})

    for inc in incomes_this_month:
        key = inc.date.strftime('%d %b')
        chart_data[key]['income'] += float(inc.amount) * CURRENCY_RATES.get(inc.currency.upper(), 1)

    for exp in expenses_this_month:
        key = exp.date.strftime('%d %b')
        chart_data[key]['expense'] += float(exp.amount) * CURRENCY_RATES.get(exp.currency.upper(), 1)

    labels = list(chart_data.keys())
    income_values = [chart_data[label]['income'] for label in labels]
    expense_values = [chart_data[label]['expense'] for label in labels]

    context = {
        'accounts': accounts,
        'incomes': incomes_this_month,
        'expenses': expenses_this_month,
        'total_income_uzs': total_income_uzs_fmt,
        'total_expense_uzs': total_expense_uzs_fmt,
        'total_balance_uzs': total_balance_uzs_fmt,
        'labels': json.dumps(labels),
        'income_values': json.dumps(income_values),
        'expense_values': json.dumps(expense_values),
    }

    return render(request, 'dashboard.html', context)

from django.db.models import Sum, Q
from datetime import datetime, timedelta

@login_required
def financial_analysis_api(request):
    """Moliyaviy tahlil ma'lumotlari (JSON)"""
    period = request.GET.get('period', 'month')
    user = request.user
    today = datetime.now().date()

    # Sana oralig'ini aniqlash
    if period == 'day':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(day=31)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
            end_date = next_month - timedelta(days=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
    else:
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(day=31)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
            end_date = next_month - timedelta(days=1)

    # Kirimlarni olish
    incomes = Income.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).values('date').annotate(total=Sum('amount')).order_by('date')

    # Chiqimlarni olish
    expenses = Expense.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).values('date').annotate(total=Sum('amount')).order_by('date')

    # Ma'lumotlarni formatlash
    income_dict = {str(item['date']): float(item['total']) for item in incomes}
    expense_dict = {str(item['date']): float(item['total']) for item in expenses}

    # Barcha sanalarni to'plash
    all_dates = set(income_dict.keys()) | set(expense_dict.keys())
    all_dates = sorted(all_dates)

    # Label'larni formatlash
    labels = []
    income_data = []
    expense_data = []

    for date_str in all_dates:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        if period == 'day':
            labels.append(date_obj.strftime('%H:00'))
        elif period == 'week':
            labels.append(date_obj.strftime('%a'))  # Dush, Sesh, ...
        elif period == 'month':
            labels.append(date_obj.strftime('%d'))  # 1, 2, 3, ...
        elif period == 'year':
            labels.append(date_obj.strftime('%b'))  # Yan, Fev, ...

        income_data.append(income_dict.get(date_str, 0))
        expense_data.append(expense_dict.get(date_str, 0))

    # JSON formatda qaytarish
    return JsonResponse({
        'labels': labels,
        'income': income_data,
        'expense': expense_data,
    })



def logout_view(request):
    logout(request)
    return redirect("home")


def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Parollar mos emas")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Bunday username mavjud")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        messages.success(request, "Ro'yxatdan muvaffaqiyatli o'tdingiz")
        login(request, user)
        return redirect("dashboard")

    return render(request, "register.html")











@login_required
def income_list(request):
    incomes = Income.objects.filter(user=request.user)
    return render(request, "incomes/list.html", {
        "incomes": incomes
    })


@login_required
def add_income(request):
    if request.method == "POST":
        #  USERNI FORMGА UZATAMIZ
        form = IncomeForm(request.POST, user=request.user)

        if form.is_valid():
            with transaction.atomic():
                income = form.save(commit=False)
                income.user = request.user
                income.save()

                # 👇 BALANSNI OSHIRAMIZ
                if income.account:
                    account = income.account

                    if account.currency != income.currency:
                        form.add_error('currency', 'Hisob valyutasi mos emas')
                        raise ValueError("Currency mismatch")

                    account.balance += income.amount
                    account.save()

            return redirect("income-list")
    else:
        #  BU YERDA HAM USER SHART
        form = IncomeForm(user=request.user)

    return render(request, "incomes/create.html", {
        "form": form
    })


@login_required
def expense_list(request):
    expenses = Expense.objects.filter(user=request.user)

    # jami chiqimlar summa
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_expense_formatted = f"{total_expense:,.0f}"  # 1,000,000 tarzida

    return render(request, "expenses/list.html", {
        "expenses": expenses,
        "total_expense": total_expense_formatted
    })


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, user=request.user)

        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user

            account = expense.account

            #  balansdan ayiramiz
            account.balance -= expense.amount
            account.save()

            expense.save()

            return redirect('expense-list')
    else:
        form = ExpenseForm(user=request.user)

    return render(request, 'expenses/create.html', {
        'form': form
    })


from django.db.models import Sum

@login_required
def account_list(request):
    accounts = Account.objects.filter(user=request.user).order_by('-created_at')

    # Har bir account uchun dinamik balans hisoblash
    for acc in accounts:
        income_sum = acc.incomes.aggregate(total=Sum('amount'))['total'] or 0
        expense_sum = acc.expenses.aggregate(total=Sum('amount'))['total'] or 0
        acc.dynamic_balance = income_sum - expense_sum  # HTMLda {{ item.dynamic_balance }} ishlatamiz

    return render(request, "accounts/list.html", {
        "accounts": accounts
    })


@login_required
def add_account(request):
    if request.method == "POST":
        form = AccountForm(request.POST)
        if form.is_valid():
            acc = form.save(commit=False)
            acc.user = request.user
            acc.save()
            return redirect("account-list")
    else:
        form = AccountForm()

    return render(request, "accounts/create.html", {
        "form": form
    })




# # REPORTS (HISOBOTLAR)
# @login_required
# def reports(request):
#     expenses = Expense.objects.filter(user=request.user)
#
#     return render(request, "reports/index.html", {
#         "expenses": expenses,
#     })




from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from datetime import date, timedelta
import calendar
import json

def reports_view(request):
    today = date.today()
    current_month = today.month

    #  Kategoriya bo‘yicha chiqimlar
    category_data = (
        Expense.objects
        .filter(date__month=current_month)
        .values('category__name')
        .annotate(total=Sum('amount'))
    )
    categories = [c['category__name'] for c in category_data]
    category_totals = [float(c['total']) for c in category_data]

    #  Oxirgi 6 oy chiqimlari
    monthly_data = (
        Expense.objects
        .annotate(month=ExtractMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # Oxirgi 6 oy ro‘yxati
    months = []
    month_totals = []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        months.append(calendar.month_abbr[m])
        month_totals.append(0)

    for m_data in monthly_data:
        idx = int(m_data['month']) - 1
        month_totals[idx] = float(m_data['total'])

    context = {
        'categories': json.dumps(categories),
        'category_totals': json.dumps(category_totals),
        'months': json.dumps(months),
        'month_totals': json.dumps(month_totals),
    }

    return render(request, 'reports/index.html', context)


# SETTINGS (PROFIL)
@login_required
def settings_view(request):
    user = request.user

    # 🔥 ENG MUHIM QATOR
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('settings')

    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    return render(request, 'settings/index.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

