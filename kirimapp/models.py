from django.db import models
from django.contrib.auth.models import User


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="incomes")
    source = models.CharField(max_length=100)   # Manba (Maosh, Freelance)
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=[('UZS','UZS'),('USD','USD'),('EUR','EUR')], default='UZS')
    account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='incomes', null=True, blank=True)
    date = models.DateField()   # foydalanuvchi tanlashi uchun
    time = models.TimeField(null=True, blank=True)  # ixtiyoriy
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.source} - {self.amount} {self.currency}"


class Expense(models.Model):
    CURRENCY_CHOICES = [
        ('UZS', 'UZS'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='UZS'
    )

    date = models.DateField()

    time = models.TimeField(null=True, blank=True)

    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'type': 'expense'}
    )

    account = models.ForeignKey(
        'Account',
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    receiver = models.CharField(
        max_length=150,
        help_text="Qabul qiluvchi / Do‘kon"
    )

    note = models.TextField(
        blank=True,
        help_text="Izoh (ixtiyoriy)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.receiver}"

class Category(models.Model):
    CATEGORY_TYPE = (
        ('income', 'Kirim'),
        ('expense', 'Chiqim'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=7, choices=CATEGORY_TYPE)

    class Meta:
        unique_together = ('user', 'name', 'type')

    def __str__(self):
        return f"{self.name} - {self.type}"


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)  # UZS, USD, EUR
    name = models.CharField(max_length=20)

    class Meta:
        verbose_name_plural = "Currencies"

    def __str__(self):
        return self.code






class Transaction(models.Model):
    INCOME_TYPES = [
        ('MONTHLY', 'Oylik'),
        ('ADVANCE', 'Avans'),
        ('BONUS', 'Bonus'),
        ('FREELANCE', 'Frilans'),
        ('OTHER', 'Boshqa'),
    ]

    CURRENCY_CHOICES = [
        ('UZS', 'UZS'),
        ('USD', 'USD'),
        ('EUR', 'EUR'),
    ]

    TRANSACTION_TYPES = [
        ('income', 'Kirim'),
        ('expense', 'Chiqim'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UZS')

    # Kirim uchun
    type = models.CharField(max_length=20, choices=INCOME_TYPES, null=True, blank=True)

    # Chiqim uchun (keyinchalik qo'shish uchun)
    category = models.CharField(max_length=50, null=True, blank=True)

    account = models.ForeignKey('Account', on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.user.username} - {self.amount} {self.currency} ({self.date})"






class Account(models.Model):
    ACCOUNT_TYPES = (
        ('CARD', 'Karta'),
        ('CASH', 'Naqd'),
        ('BANK', 'Bank hisob'),
        ('EWALLET', 'Elektron hamyon'),
    )

    CURRENCY_CHOICES = (
        ('UZS', 'So‘m'),
        ('USD', 'Dollar'),
        ('EUR', 'Yevro'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='accounts'
    )

    type = models.CharField(
        max_length=10,
        choices=ACCOUNT_TYPES
    )
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UZS')

    bank_name = models.CharField(max_length=100, blank=True, null=True)
    last_four_digits = models.CharField(max_length=4, blank=True, null=True)
    expiry_date = models.CharField(max_length=5, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    color = models.CharField(max_length=20, default='gray')   # frontend badge / icon rangi
    icon = models.CharField(max_length=30, default='wallet')  # lucide icon nomi

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'last_four_digits'],
                name='unique_user_card'
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.currency})"


# SETTINGS (PROFIL)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return self.user.username


# =====================
# Category
# =====================



