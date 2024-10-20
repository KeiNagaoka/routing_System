import os
import django

# Djangoの設定を環境変数から取得
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "routingSystem.settings")  # プロジェクト名に変更
django.setup()

import osmnx as ox
from tqdm import tqdm
import pandas as pd
from routing.models import Spot, Node
from routingSystem.backend.data_management import get_spot_df
from routingSystem.backend.core.utils import str2list_strings,get_spot_info_from_csv
from routingSystem.backend.tsp_solve import G

def add_spots():
    spot_info = get_spot_info_from_csv()

    # 重複行に対して
    duplicated_rows = spot_info[spot_info.duplicated(subset='name', keep=False)]
    spot_info = spot_info.drop_duplicates(subset='name', keep='first')
    for _, row in duplicated_rows.iterrows():
        name = row["name"]
        tags = row["tags"]
        first_row_index = spot_info[spot_info['name'] == name].index[0]
        spot_info.at[first_row_index, 'tags'] += tags
    spot_info["tags"] = spot_info["tags"].apply(lambda L:list(set(L)))
    print(f"duplicated_rows:{len(duplicated_rows)}")
    
    for idx, spot_data in spot_info.iterrows():
        spot = Spot(
            name = spot_data["name"],
            latitude = spot_data["lat"],
            longitude = spot_data["lon"],
            tags = str2list_strings(spot_data["tags"]),
            hp = spot_data["hp"],
        )
        spot.save()

# node_dfのもととなるNodeモデルを作る
def create_node_df(G=G):
    spot_info_df = get_spot_df()

    node_dict = dict({})
    for _, row in tqdm(spot_info_df.iterrows(), total=len(spot_info_df), desc="CREATE NODE DF"):
        spot_name = row["name"]
        spot_tags = row["tags"]
        node_id = ox.distance.nearest_nodes(G, row["lon"], row["lat"])
        node_data = G.nodes[node_id]
        node_lat = node_data['y']  # 緯度
        node_lon = node_data['x']  # 経度

        if node_id not in node_dict.keys():
            node_dict[node_id] = {
                "node":node_id,
                "lat":node_lat,
                "lon":node_lon,
                "name":[spot_name],
                "tags":spot_tags,
            }
        else:
            node_dict[node_id]["name"] += [spot_name]
            node_dict[node_id]["tags"] = node_dict[node_id]["tags"] + spot_tags
    node_list = [data for data in node_dict.values()]
    node_df = pd.DataFrame(node_list)
    node_df["tags"] = node_df["tags"].apply(lambda L:list(set(L)))

    for _, row in node_df.iterrows():
        node = Node(
            node = row["node"],
            name = row["name"],
            latitude = row["lat"],
            longitude = row["lon"],
            tags = row["tags"],
        )
        node.save()



if __name__ == "__main__":
    Spot.objects.all().delete()
    Node.objects.all().delete()
    add_spots()
    print("SPOTS added successfully.")
    create_node_df()
    print("NODES added successfully.")
