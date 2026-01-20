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
    'USD': 12500, # 1 USD = 12 500 UZS
    'EUR': 13500, # 1 EUR = 13 500 UZS
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
    today = now()
    start_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    incomes_this_month = incomes.filter(created_at__gte=start_month)
    expenses_this_month = expenses.filter(created_at__gte=start_month)

    # ======================
    # 3. JAMI KIRIM, CHIQIM VA UMUMIY BALANS (UZS ga konvertatsiya)
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
        key = inc.created_at.strftime('%d %b')
        chart_data[key]['income'] += float(inc.amount) * CURRENCY_RATES.get(inc.currency.upper(), 1)

    for exp in expenses_this_month:
        key = exp.created_at.strftime('%d %b')
        chart_data[key]['expense'] += float(exp.amount) * CURRENCY_RATES.get(exp.currency.upper(), 1)

    labels = list(chart_data.keys())
    income_values = [chart_data[label]['income'] for label in labels]
    expense_values = [chart_data[label]['expense'] for label in labels]

    # ======================
    # 6. Context va render
    # ======================
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

from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from django.utils import timezone


@login_required
def financial_analysis_api(request):
    """Moliyaviy tahlil ma'lumotlari (JSON)"""
    period = request.GET.get('period', 'month')
    user = request.user
    now = timezone.now()

    # Sana oralig'ini aniqlash
    if period == 'day':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        trunc_function = TruncHour('created_at')
        date_format = '%H:00'
    elif period == 'week':
        # Haftaning boshini topish (Dushanba)
        start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
        trunc_function = TruncDate('created_at')
        date_format = '%a'  # Mon, Tue, Wed...
    elif period == 'month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Keyingi oyning 1-kunini topib, 1 kun ayiramiz
        if now.month == 12:
            end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0)
            end_date = next_month - timedelta(seconds=1)
        trunc_function = TruncDate('created_at')
        date_format = '%d'  # 01, 02, 03...
    elif period == 'year':
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59)
        trunc_function = TruncMonth('created_at')
        date_format = '%b'  # Jan, Feb, Mar...
    else:
        # Default: month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end_date = now.replace(month=12, day=31, hour=23, minute=59, second=59)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0)
            end_date = next_month - timedelta(seconds=1)
        trunc_function = TruncDate('created_at')
        date_format = '%d'

    # Kirimlarni olish
    incomes = Income.objects.filter(
        user=user,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).annotate(
        period=trunc_function
    ).values('period').annotate(
        total=Sum('amount')
    ).order_by('period')

    # Chiqimlarni olish
    expenses = Expense.objects.filter(
        user=user,
        created_at__gte=start_date,
        created_at__lte=end_date
    ).annotate(
        period=trunc_function
    ).values('period').annotate(
        total=Sum('amount')
    ).order_by('period')

    # Ma'lumotlarni lug'atga joylash
    income_dict = {}
    for item in incomes:
        # period ni string formatiga o'tkazamiz (kalit sifatida ishlatish uchun)
        key = item['period'].strftime('%Y-%m-%d %H:%M:%S')
        income_dict[key] = float(item['total'])

    expense_dict = {}
    for item in expenses:
        key = item['period'].strftime('%Y-%m-%d %H:%M:%S')
        expense_dict[key] = float(item['total'])

    # Barcha vaqt oralig'ini yaratish
    labels = []
    income_data = []
    expense_data = []

    if period == 'day':
        # 24 soat
        for i in range(24):
            period_time = start_date + timedelta(hours=i)
            key = period_time.strftime('%Y-%m-%d %H:%M:%S')

            labels.append(period_time.strftime(date_format))
            income_data.append(income_dict.get(key, 0))
            expense_data.append(expense_dict.get(key, 0))

    elif period == 'week':
        # 7 kun
        for i in range(7):
            period_time = start_date + timedelta(days=i)
            # TruncDate 00:00:00 vaqtni qaytaradi
            key = period_time.replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

            labels.append(period_time.strftime(date_format))
            income_data.append(income_dict.get(key, 0))
            expense_data.append(expense_dict.get(key, 0))

    elif period == 'month':
        # Oyning barcha kunlari
        current_date = start_date
        while current_date <= end_date:
            key = current_date.strftime('%Y-%m-%d %H:%M:%S')

            labels.append(current_date.strftime(date_format))
            income_data.append(income_dict.get(key, 0))
            expense_data.append(expense_dict.get(key, 0))

            current_date += timedelta(days=1)
            current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)

    elif period == 'year':
        # 12 oy
        for month in range(1, 13):
            period_time = start_date.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
            key = period_time.strftime('%Y-%m-%d %H:%M:%S')

            labels.append(period_time.strftime(date_format))
            income_data.append(income_dict.get(key, 0))
            expense_data.append(expense_dict.get(key, 0))

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

def convert_currency(amount, from_currency, to_currency):
    """
    amount: Decimal
    from_currency: 'USD'
    to_currency: 'UZS'
    """
    if from_currency == to_currency:
        return amount

    amount_in_uzs = amount * CURRENCY_RATES[from_currency]
    return amount_in_uzs / CURRENCY_RATES[to_currency]


# CURRENCY_RATES = {
#     'UZS': 1,
#     'USD': 12500, # 1 USD = 12 500 UZS
#     'EUR': 13500, # 1 EUR = 13 500 UZS
# }
# Kirim qo'shishda uzs hisobga usd euro qoshsa boladi va hisoblashda
# CURRENCY_RATES shu orqali default ishlashdi  kelajakda reja qilib qoydim real api bilan ishlashni
# bu loyihani takomilashitirshni

@login_required
def add_income(request):
    if request.method == "POST":
        form = IncomeForm(request.POST, user=request.user)

        if form.is_valid():
            with transaction.atomic():
                income = form.save(commit=False)
                income.user = request.user
                income.save()

                if income.account:
                    account = income.account

                    #  VALYUTA KONVERTATSIYA
                    converted_amount = convert_currency(
                        income.amount,
                        income.currency,
                        account.currency
                    )

                    account.balance += converted_amount
                    account.save()

            return redirect("income-list")
    else:
        form = IncomeForm(user=request.user)

    return render(request, "incomes/create.html", {
        "form": form
    })

@login_required
def expense_list(request):
    # Foydalanuvchining barcha chiqimlarini oxirgi qo‘shilgan bo‘yicha olish
    expenses = Expense.objects.filter(user=request.user).order_by('-created_at')

    # Jami chiqimlar (UZS, USD, EUR aralash bo'lsa, valyutani o'zgartirish kerak)
    # Agar siz CURRENCY_RATES bilan UZS ga hisoblamoqchi bo'lsangiz
    CURRENCY_RATES = {
        'UZS': 1,
        'USD': 12500,
        'EUR': 13500,
    }
    total_expense = sum(
        float(exp.amount) * CURRENCY_RATES.get(exp.currency.upper(), 1)
        for exp in expenses
    )
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









from django.shortcuts import render
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from datetime import date
import calendar
import json


# Hisobotlar
@login_required
def reports_view(request):
    today = date.today()
    current_month = today.month

    # ======================
    # 1. Kategoriya bo‘yicha chiqimlar (bu oy)
    # ======================
    category_data = (
        Expense.objects
        .filter(created_at__month=current_month)  # date__month o'rniga created_at__month
        .values('category__name')
        .annotate(total=Sum('amount'))
    )

    categories = [c['category__name'] if c['category__name'] else "Noma’lum" for c in category_data]
    category_totals = [float(c['total']) for c in category_data]

    # ======================
    # 2. Oxirgi 6 oy chiqimlari
    # ======================
    monthly_data = (
        Expense.objects
        .annotate(month=ExtractMonth('created_at'))  # date -> created_at
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    # Oxirgi 6 oy ro‘yxati va default 0 bilan
    months = []
    month_totals = []
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        months.append(calendar.month_abbr[m])
        month_totals.append(0)

    # Monthly data ni moslashtiramiz
    for m_data in monthly_data:
        idx = (int(m_data['month']) - today.month + 12) % 12
        if idx < 6:  # faqat oxirgi 6 oy ichida bo‘lsa
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

    #  ENG MUHIM QATOR
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

