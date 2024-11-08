

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path('signup/', views.SignupView.as_view(), name="signup"), # アカウント登録
    path('login/', views.LoginView.as_view(), name="login"), # ログイン
    path('logout/', views.CustomLogoutView.as_view(), name="logout"), # ログアウト
    path('routesearch/', views.SearchingView.as_view(), name="routesearch"), # 経路探索
    path('instruction/', views.InstructionView.as_view(), name="instruction"), # 経路探索
    path('save_route/', views.SaveRouteView.as_view(), name="save_route"), # 経路保存処理
    path('add_user_tag/', views.AddTagView.as_view(), name="add_user_tag"), # タグ登録
    path('delete_user_tag/', views.DeleteTagView.as_view(), name="delete_user_tag"), # タグ削除
    path('get_spot_tag/', views.GetSpotTagView.as_view(), name="get_spot_tag"), # スポットに対するタグを取得
    path('routesearch/get_coordinates/', views.GetCoordView.as_view(), name="get_coordinates"), # 経路探索
    path('routesearch/change_spot_num/', views.ChangeSpotNum.as_view(), name="change_spot_num"), # スポット数変更
    path('display/', views.SpotlistView.as_view(), name='display'),
    path('update_tag/', views.UpdateTagView.as_view(), name='update_tag'), # タグ更新
    path('route_display/', views.RouteInfoView.as_view(), name='route_display'), # 経路詳細表示
    path('all_spot/', views.AllSpotView.as_view(), name='all_spot'),
    path('all_spot_only/', views.AllSpotOnlyView.as_view(), name='all_spot_only'),
]

# 静的ファイルの設定
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 404エラーのカスタムページを設定
handler404 = views.custom_404_view
handler500 = views.custom_500_view
