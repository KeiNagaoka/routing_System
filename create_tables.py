import os
import django

# Djangoの設定を環境変数から取得
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "routingSystem.settings")  # プロジェクト名に変更
django.setup()

import osmnx as ox
from tqdm import tqdm
import pandas as pd
import networkx as nx
import numpy as np
import pickle
import ujson
from routing.models import Spot, Node, Tag
from routingSystem.backend.data_management import get_spot_df, get_node_df, get_spots_data
from routingSystem.backend.core.utils import base_path, get_setting, str2list_strings,get_spot_info_from_csv


settings = get_setting()
ROAD_NETWORK = os.path.join(base_path,settings["folder_path"],settings["road_network"])
# Pickleファイルからデータをロード
with open(ROAD_NETWORK, "rb") as f:
	G = pickle.load(f)


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

def create_tag():
    _, all_tags = get_spots_data()
    for tag in tqdm(all_tags, total=len(all_tags),desc="TAG:"):
        tag_instance = Tag(
            user = None,
            tag = tag
        )
        tag_instance.save()



def create_adjacent_matrix(G=G,settings=settings):
    node_df = get_node_df()
    node_list = node_df.index.tolist()
    distance_dict = dict({})
    for start_node in tqdm(node_list, total=len(node_list), desc="ADJ MATRIX:"):
        # 最短距離を計算
        shortest_paths = nx.single_source_dijkstra_path_length(G, source=start_node, weight="length")
        distance_dict[start_node] = shortest_paths

    adj_matrix = np.array([[distance_dict[node1][node2] 
                            for node1 in node_list]
                            for node2 in node_list])
    index_node = {index:node for index, node in enumerate(node_list)}

    # 保存機能
    ADJACENT_MATRIX_PATH = os.path.join(base_path,settings["folder_path"],settings["adjacent_matrix"])
    INDEX_NODE = os.path.join(base_path,settings["folder_path"],settings["index_to_node"])
    np.save(ADJACENT_MATRIX_PATH, adj_matrix)  # 'my_array.npy'という名前で保存

    with open(INDEX_NODE, "w", encoding="utf-8") as f:
        ujson.dump(index_node, f)




if __name__ == "__main__":
    Spot.objects.all().delete()
    Node.objects.all().delete()
    Tag.objects.all().delete()
    add_spots()
    print("SPOTS added successfully.")
    create_node_df()
    print("NODES added successfully.")
    create_tag()
    print("TAG added successfully.")
    create_adjacent_matrix()
