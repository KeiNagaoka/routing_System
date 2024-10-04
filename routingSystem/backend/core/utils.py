from shapely.geometry import LineString
import pandas as pd
import ujson
import os
import sys
sys.path.append('..')
abs_path = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.join(abs_path,'..')

def fix_coordinates(row):
    coords = row['geometry'].coords
    fixed_coords = [(lat, lon) for lon, lat in coords]
    return LineString(fixed_coords)

def get_setting(base_path=base_path):
    print(f"settings:{base_path}")
    # 設定ファイルを読み込み
    SETTING_PATH = os.path.join(base_path, "settings.json")
    with open(SETTING_PATH, "r", encoding="utf-8") as json_file:
        settings = ujson.load(json_file)
    return settings

settings = get_setting()

def get_spot_info(base_path=base_path):
    print(f"get_spot_info:{base_path}")
    SPOT_INFO_PATH = os.path.join(base_path,settings["folder_path"],settings["spot_info"])
    spot_info = pd.read_csv(SPOT_INFO_PATH)
    spot_info["tags"] = spot_info["tags"].apply(str2list_strings)
    spot_info["tags"] = spot_info["tags"].apply(lambda L:[i for i in L if i!=''])
    return spot_info

def str2list_strings(string):
    if isinstance(string, list):
        return string
    else:
        return string.replace('"','').replace("'","").strip('[]').split(', ')