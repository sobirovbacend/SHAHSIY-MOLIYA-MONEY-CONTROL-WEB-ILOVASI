from django.contrib import admin
from .models import Currency, Account, Category, Transaction,Expense

admin.site.register(Currency)
admin.site.register(Account)
admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Expense)

