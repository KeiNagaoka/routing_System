from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path('signup/', views.SignupView.as_view(), name="signup"), # アカウント登録
    path('login/', views.LoginView.as_view(), name="login"), # ログイン
    path('logout/', views.LogoutView.as_view(), name="logout"), # ログアウト
    path('routesearch/', views.SearchingView.as_view(), name="routesearch"), # 経路探索
    path('routesearch/get_coordinates/', views.GetCoordView.as_view(), name="get_coordinates"), # 経路探索
    path('display/', views.SpotlistView.as_view(), name='display'),
    path('update_tag/', views.UpdateTagView.as_view(), name='update_tag'), # タグ更新
    path('route_display/', views.RouteInfoView.as_view(), name='route_display'), # 経路詳細表示
]

# 静的ファイルの設定
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
