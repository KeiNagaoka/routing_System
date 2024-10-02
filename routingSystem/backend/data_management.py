import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.utils import get_setting, get_spot_info

settings = get_setting()

def get_spots_data():
    spot_info = get_spot_info()
    added_tags = ["追加タグ1"]
    spots_data = [
        {'id': idx,
         'name': row["name"],
         'tags': row["tags"],
         'added_tags': added_tags,
         'tag_length':len(row["tags"]) + len(added_tags)
         }
        for idx, row in spot_info.iterrows()
    ]
    return spots_data

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