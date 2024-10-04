import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.utils import get_setting, get_spot_info

settings = get_setting()

def get_spots_data(spot_name=None,tag_name=None):
    spot_info = get_spot_info()
    spot_info["tag_text"] = spot_info["tags"].apply(lambda tags:', '.join(tags))
    if spot_name:
        spot_info = spot_info[spot_info["name"].str.contains(spot_name, case=False, na=False)]
    if tag_name:
        spot_info = spot_info[spot_info["tag_text"].str.contains(tag_name, case=False, na=False)]
    added_tags = []
    spots_data = [
        {'id': idx,
         'name': row["name"],
         'tags': row["tags"],
         'added_tags': added_tags,
         'tag_length':len(row["tags"]) + len(added_tags)
         }
        for idx, row in spot_info.iterrows()
    ]
    if spots_data:
        spots_data[0]["added_tags"] = ["特急停車駅"]
        spots_data[0]["tag_length"] = len(spots_data[0]["tags"]) + len(spots_data[0]["added_tags"])
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