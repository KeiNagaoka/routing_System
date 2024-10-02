import osmnx as ox
import pickle
import os
import ujson

# 設定ファイルを読み込み
base_path = os.path.dirname(os.path.abspath(__file__))
SETTING_PATH = os.path.join(base_path, "settings.json")
with open(SETTING_PATH, "r", encoding="utf-8") as json_file:
    settings = ujson.load(json_file)

# パスを指定
FOLDER_PATH = os.path.join(base_path, settings["folder_path"])
RESULT_FOLDER = os.path.join(base_path, settings["result_folder"])

# output
ROAD_NETWORK = os.path.join(FOLDER_PATH, settings["road_network"])
NETWORK_VIEW = os.path.join(RESULT_FOLDER, settings["network_view"])
NETWORK_VIEW_PNG = NETWORK_VIEW.replace('.html','.png')

#osmnxのデータをデータベース化したい
# 対象地域の道路情報取得 (東京都調布市)
area = settings["area"]
city = area.split(',')[0].lower()
print(f"city:{city}")
try:
  # 道路ネットワークデータをロード
  with open(ROAD_NETWORK, "rb") as f:
    G = pickle.load(f)
except Exception as e:
  # ファイルが無かったら作る
  G = ox.graph_from_place(area, network_type="walk") #area変えたら最初だけこっち
  # データをPickleファイルに保存
  with open(ROAD_NETWORK, "wb") as f:
      pickle.dump(G, f)

# 道路グラフネットワーク可視化
fmap = ox.graph_to_gdfs(G, nodes=False).explore()
# htmlで保存
fmap.save(outfile=NETWORK_VIEW)
# pngで保存
opts = {"node_size": 5, "bgcolor": "white", "node_color": "blue", "edge_color": "blue"}
ox.plot_graph(G, show=False, save=True, filepath=NETWORK_VIEW_PNG, **opts)
