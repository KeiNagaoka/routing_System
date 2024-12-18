from django.contrib.auth import login, authenticate
from django.views import View
from django.views.generic import TemplateView, CreateView
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.views import LoginView as BaseLoginView,  LogoutView as BaseLogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .forms import SignUpForm, LoginFrom
from .models import Spot, AddedTag, User, Tag, Mapdata
import os
import sys
sys.path.append('..')
import json
import logging
from routingSystem.backend.data_management import get_spots_data, get_routes_data, filter_tag_added_spot, get_node_df, get_spot_df
from routingSystem.backend.core.utils import str2list_strings, get_spot_info_from_csv, organize_aim_tags, get_setting, valid_search
from routingSystem.backend.tsp_solve import tsp_execute

logger = logging.getLogger(__name__)

# base_pathとsettingsを取得
base_path = os.path.dirname(os.path.abspath(__file__))
settings = get_setting()

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
            routes = get_routes_data(user)
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
    login_url = 'accounts:index'  # ログインページのURLを指定

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        user = request.user
        text = ""
        routes = []
        start_spot = ""
        goal_spot = ""
        via_spots = [{"idx":i,
                      "name":"",
                      "divclass":f"via-container{i} hide"}
                      for i in range(1,11)]
        
        _, all_tags_original = get_spots_data(user, tags_original=True)

        data = {'routes':routes,
                'text':text,
                'start_spot':start_spot,
                'goal_spot':goal_spot,
                'via_spots':via_spots,
                'via_spots_num':0,
                'all_tags': all_tags_original,
                }
        return render(request, 'routesearch.html', data)

    def post(self, request):
        text = ""
        start_spot = request.POST.get('start_spot')
        goal_spot = request.POST.get('goal_spot')
        user = request.user
        via_spots_num = int(request.POST.get('number_spot'))
        print(f"via_spots_num:{via_spots_num}/{type(via_spots_num)}")
        via_spots = [{"idx":i,
                      "name":"",
                      "divclass":f"via-container{i} hide"}
                      for i in range(1,11)]
        # 入力された経由すべき地点
        target_via_spots = []
        for i in range(1, int(via_spots_num)+1):
            spot_name = request.POST.get(f'spot{i}')
            target_via_spots.append(spot_name)
            via_spots[i-1]["name"] = spot_name
            via_spots[i-1]["divclass"] = f"via-container{i}"

        # node_dfとspot_info_df
        node_df = get_node_df(user=user)
        spot_info_df = get_spot_df(user=user)
        _, all_tags_original = get_spots_data(user, tags_original=True)


        # 目的地のタグの処理
        all_spots = spot_info_df['name'].tolist()
        all_tags = all_tags_original + all_spots
        aim_tags, invalid_tags = organize_aim_tags(target_via_spots, via_spots_num, all_tags)
        is_valid = valid_search(start_spot, goal_spot, aim_tags, all_spots)
        if len(invalid_tags)==0 and is_valid:
            print(f"aim_tags:{aim_tags}")

            route_list = tsp_execute(node_df=node_df,
                                    spot_info_df=spot_info_df,
                                    start_name=start_spot,
                                    goal_name=goal_spot,
                                    aim_tags=aim_tags,)
            # エラー発生時
            if type(route_list)==str:
                text = route_list
                route_list = []
            # 経路が見つからなかった場合
            elif len(route_list)==0:
                text = "経路を探索しましたが、条件に合う経路が見つかりませんでした。"

            data = {'routes':route_list,
                    'text':text,
                    'start_spot':start_spot,
                    'goal_spot':goal_spot,
                    'aim_tags':str(aim_tags),
                    'via_spots':via_spots,
                    'via_spots_num':via_spots_num,
                    'all_tags': all_tags_original,
                    }
        # start goal via全て同じスポットが指定された場合
        elif not is_valid:
            if start_spot not in all_spots or goal_spot not in all_spots:
                text = "出発地点と到着地点にはスポット名を入力してください。"
            else:
                text = f"{start_spot} しか通らない経路です。"
            route_list = []
            
            data = {'routes':route_list,
                    'text':text,
                    'start_spot':start_spot,
                    'goal_spot':goal_spot,
                    'aim_tags':str(aim_tags),
                    'via_spots':via_spots,
                    'via_spots_num':via_spots_num,
                    'all_tags': all_tags_original,
                    }
        else:
            # 無効なタグが入力された場合
            route_list = []
            invalid_tags = [f"「{string}」" for string in invalid_tags]
            invalid_tags_str = '、'.join(invalid_tags)
            text = f"{invalid_tags_str} は登録されていないスポット/タグです。"
            
            data = {'routes':route_list,
                    'text':text,
                    'start_spot':start_spot,
                    'goal_spot':goal_spot,
                    'aim_tags':str(aim_tags),
                    'via_spots':via_spots,
                    'via_spots_num':via_spots_num,
                    'all_tags': all_tags_original,
                    }
        
        return render(request, 'routesearch.html', data)

class SaveRouteView(View):
    def post(self, request, *args, **kwargs):
        # 受け取ったデータを読み取り
        user = request.user
        route_distance = request.POST.get('route_distance')
        route_time = request.POST.get('route_time')
        start_spot_name = request.POST.get('start_spot')
        goal_spot_name = request.POST.get('goal_spot')
        got_route_name = request.POST.get('got_route_name')
        aim_tags = request.POST.get('aim_tags')
        map_html_str = request.POST.get('map_html_str')
        via_spot_names = request.POST.get('via_spots').split(',')
        
        # Spotを参照してオブジェクトを取得
        message = ""
        try:
            start_spot = Spot.objects.get(name=start_spot_name)
            goal_spot = Spot.objects.get(name=goal_spot_name)
            via_spots = [Spot.objects.get(name=name) for name in via_spot_names if name != ""]

            # userとnameの組み合わせが既に存在するか確認
            if Mapdata.objects.filter(user=user, name=got_route_name).exists():
                print(f"user:{user}, name:{got_route_name} の組み合わせは既に存在します。")
                message = "同じ名前の経路が既に存在します。"
                data = {"message": message}
                return JsonResponse(data, status=200)

            mapdata = Mapdata.objects.create(
                user=user,
                name = got_route_name,
                distance=route_distance,
                time=route_time,
                start_spot=start_spot,
                goal_spot=goal_spot,
                aim_tags=aim_tags,
                html=map_html_str,
            )
            
            # via_spotsを設定
            mapdata.via_spots.set(via_spots)
            mapdata.save()
            message = "経路情報の保存が完了しました。"
            data = {"message": message}
            return JsonResponse(data, status=202)
        except:
            message = "経路情報が正しく保存できませんでした。"
            data = {"message": message}
            return JsonResponse(data, status=200)


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
        return render(request, "deletetag.html", data)
    
    def post(self, request):
        message = ""
        spots = []
        first_spot_tags = []

        user = request.user
        spot = request.POST.get('spot')
        tag = request.POST.get('tag')
        

        try:
            spot = Spot.objects.get(name=spot)
            AddedTag.objects.filter(user=user, tag=tag, spot=spot).delete()
            message = f"タグ 「{tag}」 がスポット 「{spot.name}」 から削除されました。"
        except Spot.DoesNotExist:
            message = "指定されたスポットが見つかりませんでした。"
        except AddedTag.DoesNotExist:
            message = "指定されたタグが見つかりませんでした。"

        # spots_dataを取得
        spots_data, _ = get_spots_data(user)
        spots_data = filter_tag_added_spot(spots_data) # spots_dataをタグが追加されたものに限定
        spots = [data["name"] for data in spots_data if data["name"] != spot]
        spot_addedtag = {data["name"]:data["added_tags"] for data in spots_data}
        if len(spots) > 0:
            first_spot_tags = spot_addedtag[spots[0]]
            data = {"text":message,
                    'spots':spots,
                    'spot_tags':first_spot_tags}
        else:
            spots = []
            first_spot_tags = []
            message = "まだタグを追加していません。「スポット情報」よりタグを追加することができます。"

        data = {"text":message,
                'spots':spots,
                'spot_tags':first_spot_tags}

        return render(request, "deletetag.html", data)
    
class InstructionView(View):
    template_name = "instruction.html"
    login_url = 'accounts:index'  # ログインページのURLを指定

    def get(self, request):
        return render(request, 'instruction.html')
    
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
        
        paginator = Paginator(spots_data, 12)  # 12個ずつ表示
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
        print(f"page_number:{page_number}")
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
        spot_id = float(request.POST.get('spot_id'))
        tag = request.POST.get('tag')

        if spot_id and tag:
            try:
                spot = Spot.objects.get(idx=spot_id)
                user = request.user  # ログインユーザーを取得
                spot_tags = str2list_strings(spot.tags)

                # AddedTagを取得
                added_tags = AddedTag.objects.filter(user=user, spot=spot)
                spot_tags += [tag.tag for tag in added_tags]
    

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


        # SpotlistViewと同じ処理
        spot_name = request.POST.get('spot_name')
        tag_name = request.POST.get('tag_name')
        
        # スポット情報のリスト (ここでは例としてリストを作成しています)
        spots_data, all_tags = get_spots_data(user=user,spot_name=spot_name,tag_name=tag_name)
        paginator = Paginator(spots_data, 12)  # 10個ずつ表示
        page_number = request.POST.get('page')
        print(f"page_number:{page_number}")
        spots = paginator.get_page(page_number)

        # POST後のリダイレクト
        values = {
            'message': 'タグが正常に追加されました。',
            'spots': spots,
            'all_tags':all_tags,
            'spot_name':spot_name,
            'tag_name':tag_name,
        }

        # POST後のリダイレクト
        return render(request, template_name, values)

# 経路の詳細情報ページ表示
class RouteInfoView(View):
    template_name  = "route_display.html"
    login_url = 'accounts:index'  # ログインページのURLを指定

    def get(self, request, template_name=template_name):
        user = request.user
        title = request.GET.get('title')
        route_list = get_routes_data(user)
        route_dict = {route["title"]:route for route in route_list}
        route = route_dict[title]
        info_json =  {
            'route': route,
            'route_id': route["id"],
            'map_html_str': route["map_html_str"],
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

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

def custom_500_view(request):
    return render(request, '500.html', status=500)
