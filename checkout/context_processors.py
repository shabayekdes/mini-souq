from .models import Cart

def cart_count(request):
    cart_count = 0
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_count = cart.cartitem_set.count()
    return {'cart_count': cart_count}
