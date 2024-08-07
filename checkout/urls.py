from django.urls import path
from . import views


urlpatterns = [
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout_page, name='checkout_page'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('order-success/', views.order_success, name='order_success'),
]
