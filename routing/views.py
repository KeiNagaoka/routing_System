from django.contrib.auth import login, authenticate
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.views import LoginView as BaseLoginView,  LogoutView as BaseLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import SignUpForm, LoginFrom
from .models import Spot, AddedTag
import sys
sys.path.append('..')
import json
from routingSystem.backend.data_management import get_spots_data, get_routes_data, filter_tag_added_spot

class IndexView(TemplateView):
    template_name = "index.html"
    login_url = 'accounts:index'  # ログインページのURLを指定

    def get(self, request, template_name=template_name):
        # スポット情報のリスト (ここでは例としてリストを作成しています)
        spots_data = get_spots_data()
        spots_data = filter_tag_added_spot(spots_data) # spots_dataをタグが追加されたものに限定
        all_tags = {"コンビニ","レストラン","公園","お気に入りスポット1"}
        
        paginator = Paginator(spots_data, 12)  # 12個ずつ表示
        page_number = request.GET.get('page')
        spots = paginator.get_page(page_number)
        routes = get_routes_data()
        info_json = {'spots': spots,
                     'routes':routes,
                     'all_tags':all_tags}

        return render(request, template_name, info_json)


class SignupView(CreateView):
    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:index")

    def form_valid(self, form):
        response = super().form_valid(form)
        name = form.cleaned_data.get("name")
        password = form.cleaned_data.get("password1")
        user = authenticate(name=name, password=password)
        login(self.request, user)
        return response


class LoginView(BaseLoginView):
    form_class = LoginFrom
    template_name = "accounts/login.html"

# LogoutViewを追加
class LogoutView(BaseLogoutView):
    success_url = reverse_lazy("accounts:index")


class SearchingView(TemplateView):
    template_name = "routesearch.html"

    def get(self, request):
        ids = [1,2,3]
        routes = [
            {'name': f'経路{id}',
             'iframe_src': f'data/user_map{id}.html',
             'distance':6512,
             'time':91,
             'via_spots': ['京王多摩川駅','調布駅','布田駅','国領駅','柴崎駅']
             }
            for id in ids
        ]
        spot_num = 1
        spot_num_range = [i for i in range(1,spot_num+1)]
        data = {'routes':routes,
                'spot_num_range':spot_num_range}
        return render(request, 'routesearch.html', data)

    def post(self, request):
        spot = request.POST.get('spot')
        number = request.POST.get('number')
        # ここでPOSTされたデータを処理するロジックを記述する
        ids = [1,2,3]
        routes = [
            {'name': f'経路{id}',
             'iframe_src': f'data/user_map{id}.html',
             'distance':6512,
             'time':91,
             'via_spots': ['京王多摩川駅','国領駅','布田駅']
             }
            for id in ids
        ]
        spot_num = 1
        spot_num_range = [i for i in range(1,spot_num+1)]
        data = {'routes':routes,
                'spot_num_range':spot_num_range}
        return render(request, 'routesearch.html', data)

class ChangeSpotNum(View):
    def post(self, request, *args, **kwargs):
        # POSTされたデータからspot_numを取得
        data = json.loads(request.body)
        spot_num = int(data.get('spot_num', 1))  # デフォルト値を1に設定

        # spot_numに基づいたリストを生成
        spot_num_range = list(range(1, spot_num + 1))

        # JSON形式で返す
        return JsonResponse({'spot_num_range': spot_num_range})


# get_coordonates.php(APIの役割)を返す
class GetCoordView(TemplateView):
    template_name = "api/get_coordinates.php"

class SpotlistView(LoginRequiredMixin, TemplateView):
    template_name = "display.html"
    login_url = 'accounts:index'  # ログインページのURLを指定

    def get(self, request, template_name=template_name):
        # スポット情報のリスト (ここでは例としてリストを作成しています)
        spots_data = get_spots_data()
        all_tags = {"コンビニ","レストラン","公園","お気に入りスポット1"}
        
        paginator = Paginator(spots_data, 12)  # 12個ずつ表示
        page_number = request.GET.get('page')
        spots = paginator.get_page(page_number)

        return render(request, template_name, {'spots': spots, 'all_tags':all_tags})

    def post(self, request, template_name=template_name):
    # スポット情報のリスト (ここでは例としてリストを作成しています)
        spots_data = [
            {'id': 1, 'name': 'スポット1', 'tags': ['公園', '観光']},
            {'id': 2, 'name': 'スポット2', 'tags': ['博物館', '文化']},
            # 他のスポットデータ...
        ]
        all_tags = {"コンビニ","レストラン","公園","お気に入りスポット1"}
        
        paginator = Paginator(spots_data, 10)  # 10個ずつ表示
        page_number = request.GET.get('page')
        spots = paginator.get_page(page_number)

        return render(request, template_name, {'spots': spots, 'all_tags':all_tags})

class UpdateTagView(View):
    def post(self, request, *args, **kwargs):
        spot_id = request.POST.get('spot_id')
        tag_name = request.POST.get('tag')

        if spot_id and tag_name:
            try:
                spot = Spot.objects.get(id=spot_id)
                user = request.user  # ログインユーザーを取得
                tag, created = Tag.objects.get_or_create(name=tag_name)  # タグを作成または取得

                # タグがスポットに既に存在するか確認し、存在しない場合のみ追加
                if not spot.tags.filter(id=tag.id).exists():
                    spot.tags.add(tag)  # スポットにタグを追加
                    spot.save()

                    # AddedTagに記録を追加
                    AddedTag.objects.create(user=user, tag=tag, spot=spot)

                    messages.success(request, f"タグ '{tag_name}' をスポット '{spot.name}' に追加しました。")
                else:
                    messages.info(request, f"タグ '{tag_name}' は既にスポット '{spot.name}' に存在します。")
            except Spot.DoesNotExist:
                messages.error(request, "指定されたスポットが見つかりませんでした。")
        else:
            messages.error(request, "タグの選択に失敗しました。")

        # POST後のリダイレクト
        return redirect('accounts:display')

# 経路の詳細情報ページ表示
class RouteInfoView(View):
    template_name  = "route_display.html"
    def get(self, request, template_name=template_name):
        route = get_routes_data()[0]
        route_id = 1
        info_json =  {
            'route': route,
            'route_id': route_id,
            'iframe_src': f'data/user_map{route_id}.html',
            }

        return render(request, template_name, info_json)