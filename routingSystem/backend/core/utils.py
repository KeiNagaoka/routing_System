from shapely.geometry import LineString
import pandas as pd
import ujson
import os
import sys
sys.path.append('..')
abs_path = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.join(abs_path,'..')
SYSTEM_PATH = os.path.join(base_path, '..', '..')
sys.path.append(SYSTEM_PATH)
from collections import Counter

def fix_coordinates(row):
    coords = row['geometry'].coords
    fixed_coords = [(lat, lon) for lon, lat in coords]
    return LineString(fixed_coords)

def get_setting(base_path=base_path):
    # 設定ファイルを読み込み
    SETTING_PATH = os.path.join(base_path, "settings.json")
    with open(SETTING_PATH, "r", encoding="utf-8") as json_file:
        settings = ujson.load(json_file)
    return settings

settings = get_setting()

def get_spot_info_from_csv(base_path=base_path):
    print(f"get_spot_info:{base_path}")
    SPOT_INFO_PATH = os.path.join(base_path,settings["folder_path"],settings["spot_info"])
    spot_info = pd.read_csv(SPOT_INFO_PATH)
    spot_info["tags"] = spot_info["tags"].apply(str2list_strings)
    spot_info["tags"] = spot_info["tags"].apply(lambda L:[i for i in L if i!=''])
    return spot_info

def get_node_df(base_path=base_path):
    NODE_DF_PATH = os.path.join(base_path,settings["folder_path"],settings["node_df"])
    node_df = pd.read_csv(NODE_DF_PATH)
    node_df["tags"] = node_df["tags"].apply(str2list_strings)
    node_df["name"] = node_df["name"].apply(str2list_strings)
    node_df["tags"] = node_df.apply(lambda row: row["tags"] + row["name"], axis=1)
    return node_df

# def get_node_df():
#     # Spotモデルからすべてのデータを取得
#     spots = Spot.objects.all()

#     # データをリストに変換
#     data = []
#     for spot in spots:
#         data.append({
#             'idx': spot.idx,
#             'name': spot.name,
#             'lat': spot.latitude,
#             'lon': spot.longitude,
#             'hp': spot.hp,
#             'tags': str2list_strings(spot.tags)
#         })

#     # リストをデータフレームに変換
#     node_df = pd.DataFrame(data)
#     print(f"node_df:{node_df}")

#     return node_df

def str2list_strings(string):
    if isinstance(string, list):
        return string
    else:
        string_list = string.strip('[]').split(', ')
        string_list = [s.strip('"').strip("'") for s in string_list]
        return string_list
    
def organize_aim_tags(request, via_spots_num, all_tags):
    aim_tags = dict({})
    aim_list = []
    for i in range(1, int(via_spots_num)+1):
        spot_name = request.POST.get(f'spot{i}')
        if spot_name in all_tags:
            aim_list.append(spot_name)
    aim_tags = dict(Counter(aim_list))
    return aim_tags

def is_passed_order(order, passed_orders):
    for passed_order in passed_orders:
        if set(order) <= set(passed_order):
            return True
    return False