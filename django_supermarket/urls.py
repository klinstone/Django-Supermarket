from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('supermarket/', include('supermarket_app.urls')),
    path('', RedirectView.as_view(pattern_name='supermarket_app:product_list',
                                  permanent=False)),
]

