from .models import CartItem

def cart_count(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = CartItem.objects.filter(cart__user=request.user).count()
    return {'cart_count': cart_count}
