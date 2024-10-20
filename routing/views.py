from django.contrib.auth import login, authenticate
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.views import LoginView as BaseLoginView,  LogoutView as BaseLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .forms import SignUpForm, LoginFrom
from .models import Spot, AddedTag, User, Tag
import sys
sys.path.append('..')
import json
from routingSystem.backend.data_management import get_spots_data, get_routes_data, filter_tag_added_spot, get_node_df, get_spot_df
from routingSystem.backend.core.utils import str2list_strings, get_spot_info_from_csv, organize_aim_tags
from routingSystem.backend.tsp_solve import tsp_execute

class IndexView(TemplateView):
    template_name = "index.html"
    login_url = 'accounts:index'  # ログインページのURLを指定

    def get(self, request, template_name=template_name):
        # スポット情報のリスト (ここでは例としてリストを作成しています)
        if not request.user.is_authenticated:
            info_json = {}
        else:
            user = request.user
            spots_data, all_tags = get_spots_data(user)
            spots_data = filter_tag_added_spot(spots_data) # spots_dataをタグが追加されたものに限定
            
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
        text = ""
        routes = []
        spot_num = 1
        spot_num_range = [i for i in range(1,spot_num+1)]

        range10 = list(range(1,11))
        data = {'routes':routes,
                'spot_num_range':spot_num_range,
                'range10':range10,
                }
        return render(request, 'routesearch.html', data)

    def post(self, request):
        text = ""
        print(f"request.POST:{request.POST}")
        start_spot = request.POST.get('start_spot')
        goal_spot = request.POST.get('goal_spot')
        user = request.user
        via_spots_num = request.POST.get('number_spot')

        # node_dfとspot_info_df
        node_df = get_node_df(user=user)
        spot_info_df = get_spot_df(user=user)

        # 目的地のタグの処理
        aim_tags = organize_aim_tags(request, via_spots_num)
        print(f"aim_tags:{aim_tags}")

        route_list = tsp_execute(node_df=node_df,
                                 spot_info_df=spot_info_df,
                                 start_name=start_spot,
                                 goal_name=goal_spot,
                                 aim_tags=aim_tags,
                                 map_html=f"user_map_{user.name}.html")
        print(f"route_list:{route_list}")
        if len(route_list)==0:
            text = "経路を探索しましたが、条件に合う経路が見つかりませんでした。"
        spot_num = 1
        spot_num_range = [i for i in range(1,spot_num+1)]

        range10 = list(range(1,11))
        data = {'routes':route_list,
                'text':text,
                'start_spot':start_spot,
                'goal_spot':goal_spot,
                'spot_num_range':spot_num_range,
                'ainm_tags':str(aim_tags),
                'range10':range10,
                }
        return render(request, 'routesearch.html', data)

class SaveRouteView(View):
    def post(self, request, *args, **kwargs):
        route_name = request.POST.get('route_name')
        route_distance = request.POST.get('route_distance')
        route_time = request.POST.get('route_time')
        start_spot = request.POST.get('start_spot')
        goal_spot = request.POST.get('goal_spot')
        aim_tags = request.POST.get('aim_tags')
        iframe_src = request.POST.get('iframe_src')
        via_spots = request.POST.get('via_spots').split(',')

        data = {"route_name":route_name,
                "route_distance":route_distance,
                "route_time":route_time,
                "start_spot":start_spot,
                "goal_spot":goal_spot,
                "aim_tags":aim_tags,
                "iframe_src":iframe_src,
                "via_spots":via_spots,
                }
        print(f"data:{data}")

        # JSON形式で返す
        return HttpResponse("経路が保存されました")

class AddTagView(TemplateView):
    template_name = "addtag.html"
    def get(self, request):
        user = request.user
        data = {}
        return render(request, 'addtag.html', data)
    
    def post(self, request):
        user = request.user
        tag = request.POST.get('tag')
        # スポット情報のリストを取得
        _, all_tags = get_spots_data(user=user)
        if tag not in all_tags:
            tag_instance = Tag(
                user = user,
                tag = tag
            )
            tag_instance.save()
            text = f"タグ「{tag}」の追加が完了しました"
        else:
            text = f"タグ「{tag}」は既に存在します。"

        data = {"text":text}

        return render(request, 'addtag.html', data)
    
class DeleteTagView(TemplateView):
    template_name = "deletetag.html"
    def get(self, request):
        text = ""
        spots = []
        first_spot_tags = []
        user = request.user
        spots_data, all_tags = get_spots_data(user)
        spots_data = filter_tag_added_spot(spots_data) # spots_dataをタグが追加されたものに限定
        if spots_data:
            spots = [data["name"] for data in spots_data]
            spot_addedtag = {data["name"]:data["added_tags"] for data in spots_data}
            first_spot_tags = spot_addedtag[spots[0]]
        else:
            text = "まだタグを追加していません。「スポット情報」よりタグを追加することができます。"
        data = {'text':text,
                'spots':spots,
                'spot_tags':first_spot_tags}
        return render(request, 'deletetag.html', data)
    
    def post(self, request):
        message = ""
        spots = []
        first_spot_tags = []

        user = request.user
        spot = request.POST.get('spot')
        tag = request.POST.get('tag')
        
        spots_data, all_tags = get_spots_data(user)
        spots_data = filter_tag_added_spot(spots_data) # spots_dataをタグが追加されたものに限定
        spots = [data["name"] for data in spots_data]
        spot_addedtag = {data["name"]:data["added_tags"] for data in spots_data}
        first_spot_tags = spot_addedtag[spots[0]]

        try:
            spot = Spot.objects.get(name=spot)
            added_tag = AddedTag.objects.get(user=user, tag=tag, spot=spot)
            added_tag.delete()
            message = f"タグ 「{tag}」 がスポット 「{spot.name}」 から削除されました。"
        except Spot.DoesNotExist:
            message = "指定されたスポットが見つかりませんでした。"
        except AddedTag.DoesNotExist:
            message = "指定されたタグが見つかりませんでした。"

        data = {"text":message,
                'spots':spots,
                'spot_tags':first_spot_tags}

        return render(request, 'deletetag.html', data)
    
class GetSpotTagView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        spot_name = request.GET.get('spot')
        spots_data, all_tags = get_spots_data(user)
        spots_data = filter_tag_added_spot(spots_data) # spots_dataをタグが追加されたものに限定
        spot_addedtag = {data["name"]:data["added_tags"] for data in spots_data}
        spot_tags = spot_addedtag[spot_name]
        data = {"spot_tags":spot_tags}

        # JSON形式で返す
        return JsonResponse(data)
    
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
        # GETリクエストからスポット名とタグ名を取得
        spot_name = request.GET.get('spot_name', "")
        tag_name = request.GET.get('tag_name', "")
        user = request.user

        # スポット情報のリストを取得
        spots_data, all_tags = get_spots_data(user=user,spot_name=spot_name,tag_name=tag_name)
        
        # ページネーション
        paginator = Paginator(spots_data, 12)  # 12個ずつ表示
        page_number = request.GET.get('page')
        spots = paginator.get_page(page_number)
        
        # コンテキストを設定
        values = {
            'spots': spots,
            'all_tags': all_tags,
            'spot_name': spot_name,
            'tag_name': tag_name,
        }

        return render(request, template_name, values)

    def post(self, request, template_name=template_name):
        spot_name = request.POST.get('spot_name')
        tag_name = request.POST.get('tag_name')
        user = request.user

        # スポット情報のリスト (ここでは例としてリストを作成しています)
        spots_data, all_tags = get_spots_data(user=user,spot_name=spot_name,tag_name=tag_name)
        
        paginator = Paginator(spots_data, 10)  # 10個ずつ表示
        page_number = request.GET.get('page')
        spots = paginator.get_page(page_number)
        values = {'spots': spots,
                  'all_tags':all_tags,
                  # 検索条件を保持するための変数
                  'spot_name':spot_name,
                  'tag_name':tag_name,
                  }

        return render(request, template_name, values)

class UpdateTagView(View):
    def post(self, request, *args, **kwargs):
        spot_id = float(request.POST.get('spot_id'))
        tag = request.POST.get('tag')

        if spot_id and tag:
            try:
                spot = Spot.objects.get(idx=spot_id)
                user = request.user  # ログインユーザーを取得
                spot_tags = str2list_strings(spot.tags)

                # タグがスポットに既に存在するか確認し、存在しない場合のみ追加
                if tag not in spot_tags:
                    # AddedTagに記録を追加
                    AddedTag.objects.create(user=user, tag=tag, spot=spot)

                    messages.success(request, f"タグ '{tag}' をスポット '{spot.name}' に追加しました。")
                else:
                    messages.info(request, f"タグ '{tag}' は既にスポット '{spot.name}' に存在します。")
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
            'iframe_src': f'map/user_map{route_id}.html',
            }

        return render(request, template_name, info_json)

# 全てのスポットとタグを取得するAPI
class AllSpotView(View):
  def get(self, request, *args, **kwargs):
    user_name = request.user.name
    user = User.objects.get(name=user_name)  # 'user'を実際のユーザー名に置き換える
    user_tags = AddedTag.objects.filter(user=user)
    added_tags = [tag.tag for tag in user_tags]

    spots = Spot.objects.all()
    tags = [tag for spot in spots for tag in str2list_strings(spot.tags)]

    combined_tags = added_tags + tags
    
    spot_df = get_spot_info_from_csv()
    spot_names = spot_df["name"].tolist()

    name_and_tags = list(set(spot_names + combined_tags))

    data = {"all_spot":name_and_tags}
    return JsonResponse(data, safe=False)

# 全てのスポットのみを返すAPI
class AllSpotOnlyView(View):
  def get(self, request, *args, **kwargs):
    
    spot_df = get_spot_info_from_csv()
    spot_names = list(set(spot_df["name"].tolist()))

    data = {"all_spot":spot_names}
    return JsonResponse(data, safe=False)
