import os
import ujson
import pickle
import numpy as np
import pandas as pd
import networkx as nx
import time
from tqdm import tqdm

# 設定ファイルを読み込み
base_path = os.path.dirname(os.path.abspath(__file__))
SETTING_PATH = os.path.join(base_path, "settings.json")
with open(SETTING_PATH, "r", encoding="utf-8") as json_file:
    settings = ujson.load(json_file)

# パスを指定
FOLDER_PATH = os.path.join(base_path, settings["folder_path"])

#input
ROAD_NETWORK = os.path.join(FOLDER_PATH, settings["road_network"])
SYMBOLS_INFO = os.path.join(FOLDER_PATH, settings["node_df"])

# output
ADJACENT_MATRIX = os.path.join(FOLDER_PATH, settings["adjacent_matrix"])

# osmnxのデータをデータベース化
# 対象地域の道路情報取得 (東京都調布市)
area = settings["area"]
city = area.split(',')[0].lower()
print(f"city:{city}")

with open(ROAD_NETWORK, "rb") as f:
    G_origin = pickle.load(f)
# 四捨五入された長さを持つ新しいグラフを作成
G = G_origin.copy()
for u, v, data in G.edges(data=True):
    if 'length' in data:
        data['length'] = np.float64(round(data['length']))

# 保存する辞書型データ
index2node = {index:node for index,node in enumerate(G.nodes)}
node2index = {node:index for index,node in enumerate(G.nodes)}

# シンボルの情報
node_df = pd.read_csv(SYMBOLS_INFO)
spot_list = node_df['node'].tolist()
timelist=[time.time()]
adj_mat = np.empty((0, len(spot_list)),dtype=np.float64)  # 初期化

# 最短距離を計算
for i,start_node in enumerate(tqdm(spot_list)):
    shortest_paths = nx.single_source_dijkstra_path_length(G, source=start_node, weight="length")
    sorted_shortest_paths = np.array([shortest_paths[key] for key in spot_list])
    if i==0:
        adj_mat = sorted_shortest_paths.copy()
    else:
        adj_mat = np.vstack((adj_mat,sorted_shortest_paths))
        
timelist.append(time.time())
print(f"\n実行時間:{int((timelist[-1]-timelist[-2])*1000)}ms")

# 配列をファイルに保存
np.save(ADJACENT_MATRIX, adj_mat)
# ファイルから配列を読み込む
loaded_array = np.load(ADJACENT_MATRIX)
index_name = {index:row['name'] for index,row in node_df.iterrows()}
names = [index_name[idx] for idx in range(len(loaded_array))]
adj_df = pd.DataFrame(loaded_array, index=names, columns=names)
ADJACENT_MATRIX_CSV = ADJACENT_MATRIX.replace('.npy','.csv')

adj_df.to_csv(ADJACENT_MATRIX_CSV,encoding="utf-8")