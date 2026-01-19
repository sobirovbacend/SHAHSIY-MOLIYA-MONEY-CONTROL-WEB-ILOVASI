from django import forms
from django.core.exceptions import ValidationError

from .models import *




class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = [
            'amount',
            'currency',
            'source',
            'account',
            'date',
            'time',
            'description'
        ]

        widgets = {
            'source': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#151b25] text-gray-900 dark:text-white text-sm',
                'placeholder': 'Masalan: Maosh, Freelance'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#151b25] text-gray-900 dark:text-white text-sm'
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#151b25] text-gray-900 dark:text-white text-sm'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#151b25] text-gray-900 dark:text-white text-sm',
                'placeholder': 'Izoh...'
            }),
            'account': forms.Select(attrs={
                'class': 'w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#151b25] text-gray-900 dark:text-white text-sm'
            }),
            'currency': forms.Select(attrs={
                'class': 'h-full px-3 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#151b25] text-gray-900 dark:text-white text-sm'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # amount alohida — chunki u currency bilan yonma-yon
        self.fields['amount'].widget.attrs.update({
            'class': 'w-full pr-24 px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-[#151b25] text-gray-900 dark:text-white text-sm',
            'placeholder': '0.00'
        })

        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user)






class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'currency', 'category', 'account', 'receiver', 'note', 'date', 'time']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'w-full pl-4 pr-24 py-3 bg-gray-50 dark:bg-[#111827]/80 border border-gray-200 dark:border-white/10 rounded-lg text-lg font-medium text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-rose-500 transition-colors'
            }),
            'currency': forms.Select(attrs={
                'class': 'absolute right-1 top-1 bottom-1 h-full px-3 bg-white dark:bg-[#151b25] rounded-md border-l border-gray-200 dark:border-white/10 text-xs font-medium text-gray-900 dark:text-white'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2.5 bg-gray-50 dark:bg-[#111827]/80 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:border-gray-400'
            }),
            'account': forms.Select(attrs={
                'class': 'w-full px-3 py-2.5 bg-gray-50 dark:bg-[#111827]/80 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:border-gray-400'
            }),
            'receiver': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2.5 bg-gray-50 dark:bg-[#111827]/80 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:border-gray-400'
            }),
            'note': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2.5 bg-gray-50 dark:bg-[#111827]/80 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:border-gray-400',
                'rows': 3
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-3 py-2.5 bg-gray-50 dark:bg-[#111827]/80 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:border-gray-400'
            }),
            'time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-3 py-2.5 bg-gray-50 dark:bg-[#111827]/80 border border-gray-200 dark:border-white/10 rounded-lg text-sm focus:outline-none focus:border-gray-400'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user, is_active=True)
            self.fields['category'].queryset = Category.objects.filter(type='expense')

    def clean(self):
        cleaned_data = super().clean()

        amount = cleaned_data.get('amount')
        account = cleaned_data.get('account')
        currency = cleaned_data.get('currency')

        if not amount or not account:
            return cleaned_data

        # 1️⃣ Valyuta mos kelishini tekshirish
        if account.currency != currency:
            raise ValidationError(
                f"Hisob valyutasi ({account.currency}) bilan chiqim valyutasi ({currency}) mos emas."
            )

        # 2️⃣ Mablag‘ yetarlimi?
        if account.balance < amount:
            raise ValidationError(
                f"Hisobda yetarli mablag‘ yo‘q. "
                f"Mavjud: {account.balance} {account.currency}"
            )

        return cleaned_data




class AccountForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = [
            'type',
            'name',
            'balance',
            'currency',
            'bank_name',
            'last_four_digits',
            'expiry_date',
        ]

        widgets = {
            'type': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-700 '
                         'bg-white dark:bg-gray-800 '
                         'text-gray-900 dark:text-gray-100 '
                         'text-sm px-3 py-2 focus:outline-none focus:ring-2 '
                         'focus:ring-gray-900 dark:focus:ring-gray-100'
            }),

            'name': forms.TextInput(attrs={
                'placeholder': 'Masalan: Asosiy karta',
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-700 '
                         'bg-white dark:bg-gray-800 '
                         'text-gray-900 dark:text-gray-100 '
                         'text-sm px-3 py-2 focus:outline-none focus:ring-2 '
                         'focus:ring-gray-900 dark:focus:ring-gray-100'
            }),

            'balance': forms.NumberInput(attrs={
                'step': '0.01',
                'placeholder': '0.00',
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-700 '
                         'bg-white dark:bg-gray-800 '
                         'text-gray-900 dark:text-gray-100 '
                         'text-sm px-3 py-2 focus:outline-none focus:ring-2 '
                         'focus:ring-gray-900 dark:focus:ring-gray-100'
            }),

            'currency': forms.Select(attrs={
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-700 '
                         'bg-white dark:bg-gray-800 '
                         'text-gray-900 dark:text-gray-100 '
                         'text-sm px-3 py-2 focus:outline-none focus:ring-2 '
                         'focus:ring-gray-900 dark:focus:ring-gray-100'
            }),

            'bank_name': forms.TextInput(attrs={
                'placeholder': 'Masalan: Kapitalbank',
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-700 '
                         'bg-white dark:bg-gray-800 '
                         'text-gray-900 dark:text-gray-100 '
                         'text-sm px-3 py-2 focus:outline-none focus:ring-2 '
                         'focus:ring-gray-900 dark:focus:ring-gray-100'
            }),

            'last_four_digits': forms.TextInput(attrs={
                'placeholder': '1234',
                'maxlength': 4,
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-700 '
                         'bg-white dark:bg-gray-800 '
                         'text-gray-900 dark:text-gray-100 '
                         'text-sm px-3 py-2 focus:outline-none focus:ring-2 '
                         'focus:ring-gray-900 dark:focus:ring-gray-100'
            }),

            'expiry_date': forms.TextInput(attrs={
                'placeholder': '12/26',
                'class': 'w-full rounded-lg border border-gray-300 dark:border-gray-700 '
                         'bg-white dark:bg-gray-800 '
                         'text-gray-900 dark:text-gray-100 '
                         'text-sm px-3 py-2 focus:outline-none focus:ring-2 '
                         'focus:ring-gray-900 dark:focus:ring-gray-100'
            }),
        }

    # === BUSINESS LOGIC VALIDATION ===
    def clean(self):
        cleaned_data = super().clean()
        acc_type = cleaned_data.get('type')

        bank_name = cleaned_data.get('bank_name')
        last_four = cleaned_data.get('last_four_digits')

        if acc_type in ['CARD', 'BANK']:
            if not bank_name:
                self.add_error('bank_name', 'Bank nomini kiriting')

            if not last_four:
                self.add_error('last_four_digits', 'Kartaning oxirgi 4 raqamini kiriting')

            if last_four and len(last_four) != 4:
                self.add_error('last_four_digits', 'Aniq 4 ta raqam bo‘lishi kerak')

        return cleaned_data


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'avatarInput'
            })
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'transaction_type',
            'amount',
            'currency',
            'type',      # income type
            'category',  # expense category
            'account',
            'date',
            'time',
            'note',
        ]
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'input-field'}),
            'amount': forms.NumberInput(attrs={'class': 'input-field'}),
            'currency': forms.Select(attrs={'class': 'input-field'}),
            'type': forms.Select(attrs={'class': 'input-field'}),
            'category': forms.Select(attrs={'class': 'input-field'}),
            'account': forms.Select(attrs={'class': 'input-field'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'input-field'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'input-field'}),
            'note': forms.Textarea(attrs={'rows': 3, 'class': 'input-field resize-none', 'placeholder': 'Izoh qoldiring...'}),
        }












