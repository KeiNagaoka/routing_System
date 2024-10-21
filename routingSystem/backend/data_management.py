import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
from core.utils import get_setting, get_spot_info_from_csv, str2list_strings
from routing.models import AddedTag, Spot, Node, Tag, Mapdata

settings = get_setting()


def get_spot_df(user=None):
    # Spotモデルから全てのデータを取得
    spots = Spot.objects.all()
    
    # データを辞書形式に変換
    data = {
        'id': [spot.idx for spot in spots],
        'name': [spot.name for spot in spots],
        'lat': [spot.latitude for spot in spots],
        'lon': [spot.longitude for spot in spots],
        'hp': [spot.hp for spot in spots],
        'tags': [spot.tags for spot in spots],
    }

    # 辞書からDataFrameを作成
    df = pd.DataFrame(data)
    df["tags"] = df["tags"].apply(str2list_strings)
    df["original_tags"] = df["tags"].copy()
    df["tags"] = df.apply(lambda row:row["tags"] + [row["name"]],axis=1)

    if user:
        df["added_tags"] = [[] for L in range(len(df))]
        added_tags = AddedTag.objects.filter(user=user)
        for tag in added_tags:
            tag_name = tag.tag
            tag_spot = tag.spot
            # tag_spotを含む行を抽出
            filtered_rows = df[df['name']==tag_spot]
            # 各行の"tags"列にtag_nameを追加
            for idx in filtered_rows.index:
                df.at[idx, 'tags'] = df.at[idx, 'tags'] + [tag_name]
                df.at[idx, 'added_tags'] = df.at[idx, 'added_tags'] + [tag_name]

    df["tags"] = df["tags"].apply(lambda L:list(set(L)))

    # インデックス指定
    df.set_index('id', inplace=True)
    
    return df

def get_spots_data(user,spot_name=None,tag_name=None):
    spot_info = get_spot_df(user=user)

    # ユーザ依存の追加タグを加える処理
    spot_info['added_tags'] = [[] for _ in range(len(spot_info))]
    added_tags = AddedTag.objects.filter(user=user)
    for tag in added_tags:
        spot_info.at[int(tag.spot.idx),'added_tags'] += str2list_strings(tag.tag)

    # 絞り込み処理
    spot_info["tag_text"] = spot_info.apply(lambda row:', '.join(row["original_tags"] + row["added_tags"]), axis=1)
    if spot_name:
        spot_info = spot_info[spot_info["name"].str.contains(spot_name, case=False, na=False)]
    if tag_name:
        spot_info = spot_info[spot_info["tag_text"].str.contains(tag_name, case=False, na=False)]

    spots_data = [
        {'id': idx,
         'name': row["name"],
         'tags': row["original_tags"],
         'added_tags': row["added_tags"]
         }
        for idx, row in spot_info.iterrows()
    ]
    
    # タグの情報
    all_tags_nested = spot_info["original_tags"].tolist() + spot_info["added_tags"].tolist()
    cleaned_list = [x for x in all_tags_nested if isinstance(x, list)]
    flattened_tags = [tag for sublist in cleaned_list for tag in sublist]
    user_added_tags = [tag.tag for tag in Tag.objects.filter(user=user)]
    all_tags = sorted(list(set(flattened_tags)) + user_added_tags)
    all_tags = [tag for tag in all_tags if tag!=""]

    return spots_data, all_tags

def get_node_df(user=None):
    # Spotモデルから全てのデータを取得
    nodes = Node.objects.all()
    
    # データを辞書形式に変換
    data = {
        'node': [node.node for node in nodes],
        'name': [node.name for node in nodes],
        'lat': [node.latitude for node in nodes],
        'lon': [node.longitude for node in nodes],
        'tags': [node.tags for node in nodes],
    }
    
    # 辞書からDataFrameを作成
    df = pd.DataFrame(data)
    df["name"] = df["name"].apply(str2list_strings)
    df["tags"] = df["tags"].apply(str2list_strings)
    df["tags"] = df.apply(lambda row:row["tags"] + row["name"],axis=1)
    
    if user:
        added_tags = AddedTag.objects.filter(user=user)
        for tag in added_tags:
            tag_name = tag.tag
            tag_spot = tag.spot
            # tag_spotを含む行を抽出
            filtered_rows = df[df['name'].apply(lambda x: tag_spot in x)]
            # 各行の"tags"列にtag_nameを追加
            for idx in filtered_rows.index:
                df.at[idx, 'tags'] = df.at[idx, 'tags'] + [tag_name]
                
    df["tags"] = df["tags"].apply(lambda L:list(set(L)))
    # インデックス指定
    df.set_index('node', inplace=True)

    return df

def filter_tag_added_spot(spots_data):
    new_spots_data = []
    for spot in spots_data:
        if spot["added_tags"]:
            new_spots_data.append(spot)
            
    return new_spots_data
    

def get_routes_data(user):
    if user:
        mapdata = Mapdata.objects.filter(user=user)

    route_list = []
    for map in mapdata:
        route = {
            'id': map.idx,
            'title': map.name,
            'created_at': map.created_at,
            'start_spot': map.start_spot.name,
            'goal_spot': map.goal_spot.name,
            'time': map.time,
            'via_spots': [spot.name for spot in map.via_spots.all()],
            'via_num': map.via_spots.count(),
            'distance': map.distance,
            'inframe_src': map.html,
        }
        route_list.append(route)
    return route_list

if __name__=="__main__":
    spots = get_spots_data()