
import sys
import os
import ujson
import pickle
import ast
import pandas as pd
import time
import folium
import osmnx as ox
import itertools
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance as dis
from core.utils import fix_coordinates, str2list_strings

# 設定ファイルを読み込み
base_path = os.path.dirname(os.path.abspath(__file__))
SETTING_PATH = os.path.join(base_path, "settings.json")
with open(SETTING_PATH, "r", encoding="utf-8") as json_file:
    settings = ujson.load(json_file)

# パスを指定
FOLDER_PATH = os.path.join(base_path, settings["folder_path"])
RESULT_FOLDER = os.path.join(base_path, settings["result_folder"])

# input
ROAD_NETWORK = os.path.join(FOLDER_PATH, settings["road_network"])
NETWORK_VIEW = os.path.join(RESULT_FOLDER, settings["network_view"])
NETWORK_VIEW_PNG = NETWORK_VIEW.replace('.html','.png')
ADJACENT_MATRIX = os.path.join(FOLDER_PATH, settings["adjacent_matrix"])
ROAD_NETWORK = os.path.join(FOLDER_PATH, settings["road_network"])
NODE_DF = os.path.join(FOLDER_PATH, settings["node_df"])
SPOT_INFO = os.path.join(FOLDER_PATH, settings["spot_info"])

# output
TSP_RESULT = os.path.join(RESULT_FOLDER, settings["tsp_result"])
RESULT_TEXT = os.path.join(FOLDER_PATH, settings["result_text"])

#コマンドライン引数を取得
args = sys.argv
aim_tags = {}
# printで確認
for i,arg in enumerate(args):
	print(f"{i}:{arg}")
for i in range(1,len(args)-1,2):
	print(f"{args[i]}->{args[i+1]}")
	if args[i] not in aim_tags.keys() and int(args[i+1]) > 0:
		aim_tags[args[i]] = int(args[i+1])
	elif aim_tags[args[i]] < int(args[i+1]):
		aim_tags[args[i]] = int(args[i+1])
print(f'aim_tags:{aim_tags}')

# 下準備
query = settings["area"]
city = query.split(',')[0].lower()

n_agent = 300
patrol = 10
max_label = 20000 #プロットするときの縦軸の上限
startNode = 0 #ここから始まる
goalNode = 625 #ここから始まる
# (nodes_dfのインデックス)
ver = "tagfill"

node_df = pd.read_csv(NODE_DF)
spot_info_df = pd.read_csv(SPOT_INFO)
node_df["tags"] = node_df["tags"].apply(str2list_strings)
spot_info_df["tags"] = spot_info_df["tags"].apply(str2list_strings)

index_spot = {index:row['node'] for index,row in node_df.iterrows()}
index_name = {index:row['name'] for index,row in node_df.iterrows()}
index_tags = {index:row['tags'] for index,row in node_df.iterrows()}
index_spot_rev = {row['node']:index for index,row in node_df.iterrows()}
name_tags = {row['name']:row['tags'] for _,row in spot_info_df.iterrows()}
name_node = {spot_name:row['node'] for _,row in node_df.iterrows() for spot_name in str2list_strings(row['name'])}
name_coord = {row['name']:[row['lat'],row['lon']] for _,row in spot_info_df.iterrows()}

count_tags = {}
for index,row in node_df.iterrows():
	for category in row['tags']:
		if category in count_tags.keys():
			count_tags[category] += 1
		else:
			count_tags[category] = 1

# raise ZeroDivisionError("ここで止める")
#データのインポート
# Pickleファイルからデータをロード
with open(ROAD_NETWORK, "rb") as f:
	G = pickle.load(f)
#ノードの属性（タグ）を更新
df_sym = pd.read_csv(NODE_DF) #csv読む

#クラス定義
class TSP:
	def __init__(self,node_df=None,adj_matrix_path=None,alpha = 1.0,beta_pre = 10.0,beta_after = 1.0,Q = 1.0,vanish_ratio = 0.95,
			  patrol_all=True,patrol=10,patrol_dict=10,kick_interval=50,kick_start=50,kick_ratio=1.1,
			  start_random=True,startNode=None,goalNode=None,index_name=index_name,
			  index_tags=index_tags,count_tags=count_tags,aim_tags=aim_tags):
		#ここから初期化処理
		#パラメータ関係
		self.alpha = alpha					# フェロモンの優先度
		self.beta = beta_pre					# ヒューリスティック情報(距離)の優先度
		self.beta_after = beta_after # 局所解に陥った後のbeta
		self.Q = Q							# フェロモン変化量の係数
		self.vanish_ratio = vanish_ratio	# 蒸発率
		#巡回都市関係
		self.patrol_dict = patrol_dict #タグごとに巡回するべき都市数
		self.n_patrol = patrol
		self.patrol_all = patrol_all #全ての都市を巡回する場合　set_loc参照
		self.cost_list = []
		self.adj_matrix_path = adj_matrix_path
		#局所解対策関係
		self.kick_cd = kick_interval #こっちは１つずつ少なくなる
		self.kick_interval = kick_interval #こっちは初期化用
		self.kick_start = kick_start
		self.kick_ratio = kick_ratio
		#スタート地点関係
		self.start_random = start_random
		self.startNode = startNode
		self.goalNode = goalNode
		#終了条件関係
		self.index_name = index_name
		self.index_tags = index_tags
		self.count_tags = count_tags #各タグを持つスポットの最大数（全都市巡回するとこのtagsになる）
		self.aim_tags = aim_tags #このタグ数満たせばいいよ
		self.now_tags = {i:0 for i in count_tags.keys()} #今のタグ数
		self.res_tags = self.now_tags.copy()
		if node_df is not None:
			node_df = pd.read_csv(node_df)
			coord_arr = np.array(node_df[['lon', 'lat']])
			self.set_loc(coord_arr) #setloc関数を呼び出して、位置座標を設定
		if adj_matrix_path is not None:
			if '.npy' in adj_matrix_path:
				self.dist = np.load(ADJACENT_MATRIX)
				print(f"self.dist:{len(self.dist)}")
			else:
				self.dist = np.array(pd.read_csv(ADJACENT_MATRIX))
				pd.DataFrame(self.dist).to_csv(ADJACENT_MATRIX,index=False)
		else:
			self.dist = dis.squareform(dis.pdist(self.loc))	# 距離の表を作成
	
	def set_loc(self,locations): #locationsは位置を表す２次元配列
		#位置座標を設定する関数
		self.loc = locations							# x,y座標
		self.n_data = len(self.loc)						# データ数
		if self.patrol_all or self.n_data<self.n_patrol: self.n_patrol = self.n_data   # 全て巡回する場合　初期化済みなので
		self.weight = np.random.random_sample((self.n_data,self.n_data))	# フェロモンの量をランダムに決める
		#フェロモンの行列　(i,j)を入れるとi×jの0~1のランダムな値が入った２次元配列
		self.result = np.arange(self.n_data)			# もっともよかった順序を保存する
		#経路をインデックスで格納　とりあえず都市0→都市1→都市2→...と通るもので初期化
		
	def cost(self,order):
		#指定された順序のコスト計算関数
		n_order = len(order)
		sum_cost = np.sum( [ self.dist[order[i],order[(i+1)%n_order]] for i in np.arange(len(order)-1) ] )
		return sum_cost
	
	def plot(self,order=None):
		#指定された順序でプロットする関数
		if order is None:
			plt.plot(self.loc[:,0],self.loc[:,1])
		else:
			plt.plot(self.loc[order,0],self.loc[order,1])
		plt.show()
	
	def save(self,printer=True):
		order_name = '\n'.join([self.index_name[i] for i in self.result])
		calls = [f"結果:{str(self.result)}",f"距離:{self.cost(self.result)}m",f"順番:\n{order_name}",f"タグ:{self.res_tags}",f"蟻数:{self.n_agent}",f"都市数:{self.n_patrol}",f"開始点:{self.startNode}",f"alpha:{self.alpha}",f"beta:{self.beta}",f"Q:{self.Q}",f"vanish_ratio:{self.vanish_ratio}",f"self.patrol_dict:{self.patrol_dict}",f"self.kick_interval:{self.kick_interval}",f"self.kick_ratio:{self.kick_ratio}",f"cost_list:{str(self.cost_list)}",f"adj_matrix_path:{self.adj_matrix_path}"]
		with open(RESULT_TEXT, mode='w') as f:
			for text in calls:
				f.write(text) #テキストに書き込み
				f.write('\n')
				# if printer: print(text) #プリントしたい場合は情報を出す

	def tag_fill(self): #tagごとに巡回が終わってるか調べる
		if not (self.aim_tags.keys() <= self.now_tags.keys()):
			raise Exception(f"巡回都市キーエラー！\n aim_tags:{self.aim_tags.keys()}はnow_tags:{self.now_tags.keys()}に含まれないよ！")
		for key_aim,val_aim in self.aim_tags.items():
			if self.now_tags[key_aim] < val_aim:
				# print(f"aim:{self.aim_tags}")
				# print(f"now:{[(key,val) for key,val in self.now_tags.items() if val > 0]}")
				return False
		return True
	
	# 局所解脱出
	def two_opt(self,route):
		improved = False
		for i in range(1, len(route) - 2):
			for j in range(i + 1, len(route)):
				if j - i == 1:
					continue  # 隣接してるところはスキップ
				new_route = route[:]
				new_route[i:j] = route[j - 1:i - 1:-1]  # reverse the section between i and j
				new_distance = self.cost(new_route)
				if new_distance < self.cost(self.result): # 現時点での最適解より良い経路なら更新
					route = new_route
					self.result = route
		if improved: # 改善できなくなるまでtwo_opt
			route = self.two_opt(route)
		return route
	
	def proposed_cities(self,now_order):
		candidate_tags = []
		if not (self.aim_tags.keys() <= self.now_tags.keys()):
			raise Exception(f"巡回都市キーエラー！\n aim_tags:{self.aim_tags.keys()}はnow_tags:{self.now_tags.keys()}に含まれないよ！")
		for key_aim,val_aim in self.aim_tags.items():
			if self.now_tags[key_aim] < val_aim:
				candidate_tags.append(key_aim)
		city = [idx for idx,tags in self.index_tags.items() if len(set(tags) & set(candidate_tags)) > 0 and idx not in now_order]
		return city

	
	# メインの部分
	def solve(self,n_agent=1000):
		self.n_agent = n_agent
		delta = np.zeros((self.n_data,self.n_data))	#フェロモン変化量
		
		if self.start_random: self.startNode = np.random.randint(self.n_data)	# 現在居る都市番号　現在地
		elif self.startNode==None: raise Exception("エラー：スタートノードを設定するか、start_randomをTrueに設定してください")

		for k in range(n_agent):
			city = np.arange(self.n_data)
			
			now_city = self.startNode
			firsttags = self.index_tags[self.startNode]
			self.now_tags = {tag:1  if tag in firsttags else 0 for tag in self.count_tags.keys()} #今のタグ数
			order = [self.startNode] 		# 巡回経路

			
			# aim_list =  {key for key, value in aim_tags.items() if value > 0}
			# city = [key for key,val in index_tags.items() if len(set(val) & aim_list) > 0 and key!=now_city]
			city = self.proposed_cities(order)
			
			#for j in range(1,self.n_patrol):
			j = 0
			while True:
				# フェロモン濃度^α × 距離の逆数^(-β)
				upper = np.power(self.weight[now_city,city],self.alpha) * np.power(self.dist[now_city,city],-self.beta)
				upper = np.where(np.isinf(upper), 0, upper) # infを0にする

				evaluation = upper / np.sum(upper)				# 評価関数
				percentage = evaluation / np.sum(evaluation)	# 移動確率
				index = self.random_index(percentage)			# 移動先の要素番号取得

				# 状態の更新
				now_city = city[ index ]
				# city = [key for key,val in index_tags.items() if len(set(val) & aim_list) > 0 and key!=now_city]
				order.append(now_city)
				city = self.proposed_cities(order)
				
				j+=1
				if len(city)==0:
					raise Exception("全ての都市を周りました！")
				
				#タグの更新
				for tag in self.index_tags[now_city]:
					if tag in self.now_tags.keys():
						self.now_tags[tag] += 1
					else:
						self.now_tags[tag] = 1
				#タグが条件を満たしていれば終了
				if self.tag_fill():
					break
				
			order.append(self.goalNode) #開始点=終了点の場合
			cost_order = self.cost(order) # 経路のコストを計算(L)
			
			# フェロモンの変化量を計算
			delta[:,:] = 0.0
			c = self.Q / cost_order
			for j in range(len(order)-1):
				delta[order[j],order[j+1]] = c
				delta[order[j+1],order[j]] = c
			
			# フェロモン更新
			self.weight *= self.vanish_ratio 
			self.weight += delta

			# 局所解脱出の処理
			self.kick_cd -= 1
			if self.kick_cd <= 0 and len(self.cost_list) >= self.kick_start: # 周回数の条件
				if self.cost(self.result)*self.kick_ratio > self.cost_list[-1]: # 今のリストがある程度短いかどうか
					order = self.two_opt(order)
					self.kick_cd = self.kick_interval
			# 定期的にフェロモン初期化
			if k%(self.n_agent/4)==0 and k > 0:
				self.weight = np.random.random_sample((self.n_data,self.n_data))	# フェロモンの量をランダムに決める
			# 後半はパラメータをいじる
			if k == self.n_agent/2:
				self.beta = self.beta_after

			self.cost_list.append(self.cost(order))

			# 今までで最も良ければ結果を更新
			if self.cost(self.result) > cost_order:
				order = self.two_opt(order)
				self.result = order.copy()
				self.res_tags = self.now_tags.copy()

			# デバッグ用
			print("Agent ... %d , Cost ... %lf" % (k,self.cost(self.result)))
			print(f'距離:{cost_order}\norder:{order}')

		return self.result

	
	def random_index(self,percentage):
		#任意の確率分布に従って乱数を生成する関数
		n_percentage = len(percentage)
		
		while True:
			index = np.random.randint(n_percentage) #0~n_percentage-1で任意のintを出す
			y = np.random.random()
			if y < percentage[index]:
				return index
			

# 必要最低限のスポットに絞る
def necessary_spots(order_name,aim_tags,name_tags=name_tags):
	tags_dict = {name:name_tags[name] for name in order_name}
	aim_tags_processed = {key:val for key,val in aim_tags.items() if val > 0}
	necessary_tags = set(aim_tags_processed.keys())
	# start_and_goal = set([order_name[0],order_name[-1]])
	start_and_goal = set(["電気通信大学正門","調布駅"])
	print(f"tags_dict:{tags_dict}")
	print(f"aim_tags_processed:{aim_tags_processed}")
	print(f"necessary_tags:{necessary_tags}")
	print(f"start_and_goal:{start_and_goal}")
	# tagsがnecessary_tagsに含まれるものだけを抽出
	
	result_order = [name for name, tags in tags_dict.items() if set(tags) & necessary_tags or name in start_and_goal]
	# result_order = []
	# for name,tags in tags_dict.items():
	# 	if len(set(tags) & necessary_tags) > 0:
	# 		result_order.append(name)
	return result_order

#実行部分
def tsp_execute(index_name=index_name):
	aim_tags_input = aim_tags
	tsp = TSP(node_df=NODE_DF,
		   adj_matrix_path=ADJACENT_MATRIX,
		   alpha = 1.0,
		   beta_pre=1.0, 
		   beta_after = 1.0, 
		   Q = 1.0,
		   vanish_ratio = 0.8,
		   aim_tags=aim_tags_input,
		   kick_ratio=1.1,
		   kick_start=100,
		   kick_interval=10,
		   count_tags=count_tags,
		   startNode=startNode,
		   goalNode=goalNode,
		   patrol_all=False,
		   patrol=patrol,
		   start_random=False)
	
	startTime = time.time()

	# メイン処理
	order = tsp.solve(n_agent=n_agent)		# n_agent匹の蟻を歩かせる
	
	name_order = [index_name[i] for i in order]
	spots_original = [name for L in name_order for name in str2list_strings(L)]
	spots = necessary_spots(spots_original,aim_tags) # これを返す
	goalTime = time.time()
	print(f"順番:\n{spots}") # これを返す
	print(f'実行時間:{goalTime-startTime:.3f}秒')
	tsp.save(printer=True)

	# ルートの隣り合う同じ値を消す
	def shrink_route(route):
		if len(route) == 0: return []
		shrunk_route = [route[0]]  # 最初の要素を追加
		for i in range(1, len(route)):
			if route[i] != route[i-1]:
				shrunk_route.append(route[i])
		return shrunk_route

	for index in G.nodes():
		G.nodes[index]['tags'] = [] #タグの初期化
		G.nodes[index]['name'] = '' #名前の初期化
	symbol_list = []
	for _,row in df_sym.iterrows():
		symbol_list.append(ox.nearest_nodes(G,row['lon'],row['lat']))
		G.nodes[symbol_list[-1]]['tags'] += ast.literal_eval(row['tags']) #タグ追加
		if G.nodes[symbol_list[-1]]['name']=='':
			G.nodes[symbol_list[-1]]['name'] = row['name']
		else:
			G.nodes[symbol_list[-1]]['name'] += ",%s"%row['name'] #名前の追加
	symbol_list = list(set(symbol_list))

	order = shrink_route([index_spot[i] for i in tsp.result])
	order = [name_node[spot_name] for spot_name in spots]
	print(f"order:{order}")

	#ルート
	pre_route_tsp = [ox.shortest_path(G,s1,s2,weight='length', cpus=1) for s1,s2 in zip(order[:-1],order[1:])]
	#出力された順番をもとにからノードを辿る
	route_tsp = shrink_route(list(itertools.chain.from_iterable(pre_route_tsp))) #平坦化
	edges_tsp = [(route_tsp[i],route_tsp[i+1],0) for i in range(len(route_tsp)-1)]
	# print(f'symbol_list:{symbol_list}')
	# print(f'edges_tsp:{edges_tsp}')
	passed_symbols = list(set(order).intersection(set(route_tsp)))
	not_passed_symbols = list(set(order).difference(set(passed_symbols)))

	#可視化
	# Folium マップを作成し、縮尺（ズーム レベル）と方位を設定
	# 最短経路を地図にプロット
	map = folium.Map()
	# エッジだけを持つ部分グラフを取得
	route_G = G.edge_subgraph(edges_tsp)

	# エッジのジオメトリ情報を含むGeoDataFrameを取得
	gdf_edges = ox.graph_to_gdfs(route_G, nodes=False)
	# geometry列の座標情報を修正

	gdf_edges['geometry'] = gdf_edges.apply(fix_coordinates, axis=1)
	gdf_edges.to_csv('edges.csv', index=False)
	

	# ジオメトリ情報を地図に追加
	for _, row in gdf_edges.iterrows():
		folium.PolyLine(locations=row['geometry'].coords, weight=5, color='red').add_to(map)  # weightを設定

	# マーカーを追加
	for i, symbol in enumerate(passed_symbols):
		print(f"{i+1:03d}:{G.nodes[symbol]['name']}")
		# loc = [G.nodes[symbol]['y'], G.nodes[symbol]['x']]
		name_list = str2list_strings(G.nodes[symbol]['name'])
		for name in name_list:
			if name in spots:
				loc = name_coord[name]
				folium.Marker(loc, popup=name, icon=folium.Icon(color='red')).add_to(map)

	# # 通っていないシンボル
	# for i, symbol in enumerate(not_passed_symbols):
	# 	loc = [G.nodes[symbol]['y'], G.nodes[symbol]['x']]
	# 	name = G.nodes[symbol]['name']
	# 	folium.Marker(loc, popup=name, icon=folium.Icon(color='blue')).add_to(map)

	# 縮尺とズームを設定
	map.fit_bounds(map.get_bounds())
	map.zoom_start = 15

	# 保存
	print(f"TSP_RESULT:{TSP_RESULT}")
	map.save(TSP_RESULT)

if __name__ == "__main__":
	tsp_execute()