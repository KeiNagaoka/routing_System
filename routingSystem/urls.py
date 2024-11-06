from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('routing.urls', namespace='accounts')),  # 名前空間を指定してインクルード
]
