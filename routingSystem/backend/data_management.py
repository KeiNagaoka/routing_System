import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.utils import get_setting, get_spot_info, str2list_strings
from routing.models import AddedTag

settings = get_setting()

def get_spots_data(user_name,spot_name=None,tag_name=None):
    spot_info = get_spot_info()
    spot_info["tag_text"] = spot_info["tags"].apply(lambda tags:', '.join(tags))
    if spot_name:
        spot_info = spot_info[spot_info["name"].str.contains(spot_name, case=False, na=False)]
    if tag_name:
        spot_info = spot_info[spot_info["tag_text"].str.contains(tag_name, case=False, na=False)]

    # ユーザ依存の追加タグを加える処理
    spot_info['added_tags'] = [[] for _ in range(len(spot_info))]
    added_tags = AddedTag.objects.filter(user__name=user_name)
    for tag in added_tags:
        spot_info.at[tag.spot.idx,'added_tags'] = tag.tag
    invalid_spot_info = spot_info[~spot_info['tags'].apply(lambda x: isinstance(x, list))]

    spots_data = [
        {'id': idx,
         'name': row["name"],
         'tags': row["tags"],
         'added_tags': str2list_strings(row["added_tags"])
         }
        for idx, row in spot_info.iterrows()
    ]
    return spots_data

def filter_tag_added_spot(spots_data):
    new_spots_data = []
    for spot in spots_data:
        if spot["added_tags"]:
            new_spots_data.append(spot)
            
    return new_spots_data
    

def get_routes_data():
    spots_data = [
        {
            'id': idx,
            'title': 'サンプル経路1',
            'start_spot': '調布駅',
            'goal_spot': '電気通信大学正門',
            'time': '2024年09月24日17時50分',
            'via_num': 2,
            'distance': 417,
        }
        for idx in range(10)
    ]
    return spots_data

if __name__=="__main__":
    spots = get_spots_data()