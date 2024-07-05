from django.contrib import admin
from django.urls import path, include
from . import settings
from django.conf.urls.static import static
from auth import views as auth_views

from checkout.views import cart_page
from checkout.views import checkout_page

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('products/', include('product.urls')),
    path('cart/', cart_page, name='cart'),
    path('checkout/', checkout_page, name='checkout'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
