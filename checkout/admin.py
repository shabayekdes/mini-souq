from django.contrib import admin

from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  # Number of extra forms to display

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_amount', 'created_at')
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)
