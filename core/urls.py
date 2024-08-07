from django.contrib import admin
from django.urls import path, include
from . import settings
from django.conf.urls.static import static
from auth import views as auth_views

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('products/', include('product.urls')),
    path('checkout/', include('checkout.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
