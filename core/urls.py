from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('products/', include('product.urls')),
    path('checkout/', include('checkout.urls')),
]

# Serves uploaded media in development only; static() is a no-op when DEBUG is
# off, so production needs external media storage (see README).
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
