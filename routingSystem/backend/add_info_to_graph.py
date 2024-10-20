from tqdm import tqdm	
import os
import ujson
import pickle
import pandas as pd
import osmnx as ox
from core.utils import str2list_strings

# 設定ファイルを読み込み
base_path = os.path.dirname(os.path.abspath(__file__))
SETTING_PATH = os.path.join(base_path, "settings.json")
with open(SETTING_PATH, "r", encoding="utf-8") as json_file:
    settings = ujson.load(json_file)
	
FOLDER_PATH = os.path.join(base_path, settings["folder_path"])
NODE_DF = os.path.join(FOLDER_PATH, settings["node_df"])
ROAD_NETWORK = os.path.join(FOLDER_PATH, settings["road_network"])


node_df = pd.read_csv(NODE_DF)
node_df["tags"] = node_df["tags"].apply(str2list_strings)
node_df["name"] = node_df["name"].apply(str2list_strings)
node_df["tags"] = node_df.apply(lambda row: row["tags"] + row["name"], axis=1)

# Pickleファイルからデータをロード
with open(ROAD_NETWORK, "rb") as f:
	G = pickle.load(f)

if __name__ == "__main__":
    for index in G.nodes():
        G.nodes[index]['tags'] = [] #タグの初期化
        G.nodes[index]['name'] = '' #名前の初期化
    symbol_list = []

    for _, row in tqdm(node_df.iterrows(), total=len(node_df), desc="node_df"):
        symbol_list.append(ox.nearest_nodes(G, row['lon'], row['lat']))
        G.nodes[symbol_list[-1]]['tags'] += str2list_strings(row['tags'])  # タグ追加
        if G.nodes[symbol_list[-1]]['name'] == '':
            G.nodes[symbol_list[-1]]['name'] = row['name']
        else:
            G.nodes[symbol_list[-1]]['name'] += ",%s" % row['name']  # 名前の追加

    symbol_list = list(set(symbol_list))
    print(f"symbol_list: {len(symbol_list)}")
    
    # Gをroad_networkに保存
    with open(ROAD_NETWORK, 'wb') as f:
        pickle.dump(G, f)