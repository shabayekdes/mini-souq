from django import forms
from .models import MAX_QUANTITY_PER_ITEM, Order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        # Whitelist, not exclude: user, totals and prices are always set on
        # the server, and new model fields must not become user-editable.
        fields = []

class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=MAX_QUANTITY_PER_ITEM, initial=1)
