
import sys
import os
import ujson
import pickle
import time
import pandas as pd
import folium
import osmnx as ox
import itertools
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import distance as dis
from core.utils import fix_coordinates, str2list_strings, is_passed_order
from data_management import get_node_df, get_spot_df

# 設定ファイルを読み込み
base_path = os.path.dirname(os.path.abspath(__file__))
SETTING_PATH = os.path.join(base_path, "settings.json")
with open(SETTING_PATH, "r", encoding="utf-8") as json_file:
    settings = ujson.load(json_file)

# パスを指定
FOLDER_PATH = os.path.join(base_path, settings["folder_path"])
RESULT_FOLDER = os.path.join(base_path, settings["result_folder"])
MAP_FOLDER = os.path.join(base_path, '..', '..', settings["static_folder"], settings["map_folder"])

# input
ROAD_NETWORK = os.path.join(FOLDER_PATH, settings["road_network"])
NETWORK_VIEW = os.path.join(RESULT_FOLDER, settings["network_view"])
NETWORK_VIEW_PNG = NETWORK_VIEW.replace('.html','.png')
ADJACENT_MATRIX = os.path.join(FOLDER_PATH, settings["adjacent_matrix"])
NODE_DF = os.path.join(FOLDER_PATH, settings["node_df"])
SPOT_INFO = os.path.join(FOLDER_PATH, settings["spot_info"])
INDEX_NODE = os.path.join(FOLDER_PATH, settings["index_to_node"])

# output
MAP_PATH = os.path.join(RESULT_FOLDER, settings["tsp_result"])
RESULT_TEXT = os.path.join(FOLDER_PATH, settings["result_text"])

# try:
if True:
	# 下準備
	query = settings["area"]
	city = query.split(',')[0].lower()

	n_agent = 300
	patrol = 10
	max_label = 20000 #プロットするときの縦軸の上限
	start_name = "調布駅"
	goal_name = "電気通信大学正門"
	# startNode = 0 #ここから始まる
	# goalNode = 625 #ここから始まる
	# (nodes_dfのインデックス)
	ver = "tagfill"

	node_df = get_node_df()
	spot_info_df = get_spot_df()
	node_df["tags"] = node_df.apply(lambda row: row["tags"] + row["name"], axis=1)
	spot_info_df["tags"] = spot_info_df["tags"].apply(str2list_strings)
	spot_info_df["tags"] = spot_info_df.apply(lambda row: row["tags"] + [row["name"]], axis=1)

	with open(INDEX_NODE, 'r') as f:
		index_node = ujson.load(f)
	index_node = {int(key):int(val) for key,val in index_node.items()}
	index_node_rev = {val:key for key,val in index_node.items()}
	index_name = {index_node_rev[node]:row['name'] for node,row in node_df.iterrows()}
	name_node = {spot_name:idx for idx,row in node_df.iterrows() for spot_name in str2list_strings(row['name'])}
	name_coord = {row['name']:[row['lat'],row['lon']] for _,row in spot_info_df.iterrows()}

	# タグ関連（ここはuserによって異なる）
	index_tags = {index_node_rev[node]:row['tags'] for node,row in node_df.iterrows()}
	name_tags = {row['name']:row['tags'] for _,row in spot_info_df.iterrows()}


	count_tags = {}
	for index,row in node_df.iterrows():
		for category in row['tags']:
			if category in count_tags.keys():
				count_tags[category] += 1
			else:
				count_tags[category] = 1

	# name_index = {row['name']:index for index,row in node_df.iterrows()}
	name_index = dict({})
	for node,row in node_df.iterrows():
		for name in str2list_strings(row['name']):
			name_index[name] = index_node_rev[node]

	# raise ZeroDivisionError("ここで止める")
	# データのインポート
	# コマンドライン引数を取得
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
# except Exception as e:
# 	print(f"エラー:{e}")

# ルートの隣り合う同じ値を消す
def shrink_route(route):
	if len(route) == 0: return []
	shrunk_route = [route[0]]  # 最初の要素を追加
	for i in range(1, len(route)):
		if route[i] != route[i-1]:
			shrunk_route.append(route[i])
	return shrunk_route

#クラス定義
# vanish_ratio:フェロモンの蒸発率(ρ)
class TSP:
	def __init__(self,node_df=None,adj_matrix_path=None,alpha = 1.0,beta_pre = 10.0,beta_after = 1.0,Q = 1.0,vanish_ratio = 0.95,
			  patrol_all=True,patrol=10,patrol_dict=10,kick_interval=50,kick_start=50,kick_ratio=1.1,
			  gamma=0.5,epsilon=0.8,passed_edges=[],output_orders=[],
			  startNode=None,goalNode=None,index_name=dict({}),
			  index_tags=dict({}),count_tags=dict({}),aim_tags=dict({})):
		#ここから初期化処理
		#パラメータ関係
		self.alpha = alpha					# フェロモンの優先度
		self.beta = beta_pre				# ヒューリスティック情報(距離)の優先度
		self.beta_after = beta_after		# 局所解に陥った後のbeta
		self.Q = Q							# フェロモン変化量の係数
		self.vanish_ratio = vanish_ratio	# 蒸発率
		self.gamma = gamma					# 通過済みエッジ　フェロモンの塗布量の制限係数
		self.epsilon = epsilon				# 通過済みエッジ　フェロモンの蒸発率
		self.passed_edges = passed_edges	# 通過済みエッジ　既に通過したためデバフをかけるエッジ
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
		self.startNode = startNode
		self.goalNode = goalNode
		#終了条件関係
		self.index_name = index_name
		self.index_tags = index_tags
		self.count_tags = count_tags #各タグを持つスポットの最大数（全都市巡回するとこのtagsになる）
		self.aim_tags = aim_tags #このタグ数満たせばいいよ
		self.now_tags = {i:0 for i in count_tags.keys()} #今のタグ数
		self.res_tags = self.now_tags.copy()

		if node_df is None:
			node_df = pd.read_csv(node_df)
		coord_arr = np.array(node_df[['lon', 'lat']])
		self.set_loc(coord_arr) #setloc関数を呼び出して、位置座標を設定

		# 蒸発率と通過済みエッジ関連（蒸発率とフェロモン制限係数）
		self.n_data = len(node_df)
		self.output_orders = output_orders
		# self.evap_matrix = np.full((self.n_data, self.n_data), self.vanish_ratio) #蒸発行列
		self.evap_matrix = self.create_evap_matrix()
		if adj_matrix_path is not None:
			if '.npy' in adj_matrix_path:
				self.dist = np.load(ADJACENT_MATRIX)
			else:
				self.dist = np.array(pd.read_csv(ADJACENT_MATRIX))
				pd.DataFrame(self.dist).to_csv(ADJACENT_MATRIX,index=False)
		else:
			self.dist = dis.squareform(dis.pdist(self.loc))	# 距離の表を作成

	def create_evap_matrix(self):
		evap_matrix = np.full((self.n_data, self.n_data), self.vanish_ratio)
		print(f"self.passed_edges:{self.passed_edges[:10]}...")
		for coord in self.passed_edges:
			evap_matrix[coord] = self.epsilon
		return evap_matrix
	
	def set_loc(self,locations): #locationsは位置を表す２次元配列
		#位置座標を設定する関数
		self.loc = locations							# x,y座標
		self.n_data = len(self.loc)						# データ数
		if self.patrol_all or self.n_data<self.n_patrol: self.n_patrol = self.n_data   # 全て巡回する場合　初期化済みなので
		self.weight = np.random.random_sample((self.n_data,self.n_data))	# フェロモンの量をランダムに決める
		#フェロモンの行列　(i,j)を入れるとi×jの0~1のランダムな値が入った２次元配列
		self.result = []			# もっともよかった順序を保存する
		#経路をインデックスで格納　とりあえず都市0→都市1→都市2→...と通るもので初期化
		
	def cost(self,order):
		# 指定された順序のコスト計算関数
		n_order = len(order)
		if n_order > 0:
			sum_cost = np.sum( [ self.dist[order[i],order[(i+1)%n_order]] for i in np.arange(len(order)-1) ] )
			return sum_cost
		else:
			return 524280
	
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
		# aim_tagsのkeyとvalを取り出し
		for key_aim,val_aim in self.aim_tags.items():
			if self.now_tags[key_aim] < val_aim:
				return False
		return True
	
	# 既に出力した経路と同じ経路ならTrue
	def passed_route(self,order):
		for route in self.output_orders:
			if set(order) == set(route):
				return True
		return False
	
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
			raise Exception(f"巡回都市キーエラー！\n aim_tags:{self.aim_tags.keys()}はnow_tags{self.now_tags.keys()}に含まれないよ！")
		for key_aim,val_aim in self.aim_tags.items():
			if self.now_tags[key_aim] < val_aim:
				candidate_tags.append(key_aim)
		city = [idx for idx,tags in self.index_tags.items() if len(set(tags) & set(candidate_tags)) > 0 and idx not in now_order]
		return city

	
	# メインの部分
	def solve(self,n_agent=1000):
		self.n_agent = n_agent
		delta = np.zeros((self.n_data,self.n_data))	#フェロモン変化量
		
		if self.startNode==None: raise Exception("エラー：スタートノードを設定してください。")

		for k in range(n_agent):
			city = [self.startNode] + [i for i in np.arange(self.n_data) if i != self.startNode and i != self.goalNode] + [self.goalNode] #巡回都市
			
			now_city = self.startNode
			# firsttags = self.index_tags[self.startNode]
			# self.now_tags = {tag:1  if tag in firsttags else 0 for tag in self.count_tags.keys()} #今のタグ数
			self.now_tags = {tag:0 for tag in self.count_tags.keys()} #今のタグ数
			order = [self.startNode] 		# 巡回経路

			
			# aim_list =  {key for key, value in aim_tags.items() if value > 0}
			# city = [key for key,val in index_tags.items() if len(set(val) & aim_list) > 0 and key!=now_city]
			city = self.proposed_cities(order)
			
			#for j in range(1,self.n_patrol):
			j = 0
			while city:
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
					
				#タグの更新
				for tag in self.index_tags[now_city]:
					if tag in self.now_tags.keys():
						self.now_tags[tag] += 1
					else:
						self.now_tags[tag] = 1
				#タグが条件を満たしていれば終了
				if not (self.aim_tags.keys() <= self.now_tags.keys()):
					# return None
					raise Exception(f"巡回都市キーエラー！\n aim_tags:{self.aim_tags.keys()}はnow_tags:{self.now_tags.keys()}に含まれないよ！")
				if self.tag_fill():
					break
				elif len(city)==0:
					# return None
					raise Exception("全ての都市を周りました！")
				
			# ゴールノードに移動
			order.append(self.goalNode) #開始点=終了点の場合
			cost_order = self.cost(order) # 経路のコストを計算(L)

			# フェロモンの変化量を計算
			delta[:,:] = 0.0
			c = self.Q / cost_order # フェロモンの変化量
			for j in range(len(order)-1):
				# 過去に巡回した通過済みエッジのフェロモンの蒸発
				if (order[j],order[j+1]) in self.passed_edges:
					delta[order[j],order[j+1]] = c * self.gamma
					delta[order[j+1],order[j]] = c * self.gamma
				# 過去に巡回した通過済みエッジのフェロモンの蒸発
				else:
					delta[order[j],order[j+1]] = c
					delta[order[j+1],order[j]] = c
			
			# フェロモン更新
			self.weight *= self.evap_matrix	# 蒸発
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
				if not self.passed_route(order):
					self.result = order.copy()
					self.res_tags = self.now_tags.copy()

			# デバッグ用
			# print("Agent ... %d , Cost ... %lf" % (k,self.cost(self.result)))
			# print(f'距離:{cost_order}, order:{order}')

		if self.result is None:
			return None
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
def necessary_spots(order_name,
					aim_tags,
					name_tags,
					passed_spot_names,
					start_name,
					goal_name):
	print(f"order_name:{order_name[:10]}...")
	tags_dict = {name:name_tags[name] for name in order_name}
	aim_tags_processed = {key:val for key,val in aim_tags.items() if val > 0}
	necessary_tags = set(aim_tags_processed.keys())
	necessary_list = [key for key, val in aim_tags_processed.items() for _ in range(val)]
	via_spots = [spot for spot in order_name if spot not in [start_name, goal_name]]

	# tagsがnecessary_tagsに含まれるものだけを抽出
	result_order = []
	# スタートとゴールだけ先に見る
	for spot in [start_name, goal_name]:
		tags = tags_dict[spot]
		result_order.append(spot)
		for tag in tags:
			if tag in necessary_tags:
				necessary_tags.remove(tag)
	# 経由地点を選別
	# 先に通過していない経由地点を優先
	via_spots_priority = [spot for spot in via_spots if spot not in passed_spot_names]
	via_spots_subord = [spot for spot in via_spots if spot in passed_spot_names]
	via_spots = via_spots_priority + via_spots_subord
	# 経由地点を選別
	for spot in via_spots:
		tags = tags_dict[spot]
		if set(tags) & set(necessary_list):
			result_order.append(spot)
			for tag in tags:
				if tag in necessary_list:
					necessary_list.remove(tag)

	# start_name, goal_nameが含まれていたら削除して最初と最後にくっつける
	if start_name in result_order:
		result_order.remove(start_name)
	if goal_name in result_order:
		result_order.remove(goal_name)
	result_order = [start_name] + result_order + [goal_name]
	
	return result_order

#実行部分
def tsp_execute(node_df,
				spot_info_df,
				start_name,
				goal_name,
				aim_tags,
				):
	timelist = []
	timelist.append(time.time())
	print("TSP EXECUTE!!!")
	print(f"start_name:{start_name}")
	print(f"goal_name:{goal_name}")
	print(f"aim_tags:{aim_tags}")
	# 前処理
	aim_tags_input = aim_tags
	startNode = name_index[start_name]
	goalNode = name_index[goal_name]
	index_tags = {index_node_rev[node]:row['tags'] for node,row in node_df.iterrows()}
	name_tags = {row['name']:row['tags'] for _,row in spot_info_df.iterrows()}

	# 入力できるタグの最大値をカウント
	count_tags = {}
	for _,row in node_df.iterrows():
		for tag in row['tags']:
			if tag in count_tags.keys():
				count_tags[tag] += 1
			else:
				count_tags[tag] = 1

	# 通過済みエッジ
	passed_edges = []
	output_orders = [] # 出力した経路
	passed_spot_names = []
	# 結果を格納するリスト
	info_json_list = []
	# 3回巡回経路探索を繰り返す
	if len(aim_tags) == 0:
		iter_num = 1
	else:
		iter_num = 5
	# Pickleファイルからデータをロード
	with open(ROAD_NETWORK, "rb") as f:
		G = pickle.load(f)

	# added_tagsを道路ネットワークデータに追加
	symbol_list = []
	node_df_filtered = node_df[node_df['added_tags'].apply(lambda L: len(L) > 0)]
	for _,row in node_df_filtered.iterrows():
		symbol_list.append(ox.nearest_nodes(G,row['lon'],row['lat']))
		G.nodes[symbol_list[-1]]['tags'] += row['tags'] #タグ追加
	symbol_list = list(set(symbol_list))

	for route_index in range(iter_num):
		print(f"route_index:{route_index+1}回目の経路探索")
		tsp = TSP(node_df=node_df,
				adj_matrix_path=ADJACENT_MATRIX,
				alpha = 0.5,
				beta_pre=0.1, 
				beta_after = 0.1, 
				Q = 1.0,
				gamma=0.3,
				epsilon=0.6,
				passed_edges=passed_edges,
				output_orders=output_orders,
				vanish_ratio = 0.8,
				aim_tags=aim_tags_input,
				kick_ratio=1.1,
				kick_start=100,
				kick_interval=10,
				index_name = index_name,
				index_tags = index_tags,
				count_tags = count_tags,
				startNode=startNode,
				goalNode=goalNode,
				patrol_all=False,
				patrol=patrol,)
		
		# メイン処理
		order = tsp.solve(n_agent=n_agent)		# n_agent匹の蟻を歩かせる
		if order is None:
			break
		elif len(order) == 0:
			break

		passed_edges += [(order[i],order[i+1]) for i in range(len(order)-1)] + [(order[i+1],order[i]) for i in range(len(order)-1)]

		# 結果を保存
		timelist.append(time.time())
		print(f"巡回経路探索:{timelist[-1]-timelist[-2]}秒")
	
		name_order = [index_name[i] for i in order]
		spots_original = [name for L in name_order for name in str2list_strings(L)]
		spots = necessary_spots(spots_original,
						  aim_tags_input,
						  name_tags,
						  passed_spot_names=passed_spot_names,
						  start_name=start_name,
						  goal_name=goal_name)
		
		# 出力したスポットと経路を保存
		passed_spot_names = passed_spot_names + spots
		print(f"order:{order}")
		print(f"output_orders:{output_orders}")
		if not is_passed_order(order,output_orders):
			output_orders.append(order)
		else:
			continue

		timelist.append(time.time())
		print(f"nearest_nodes:{timelist[-1]-timelist[-2]}秒")

		order = shrink_route([index_node[i] for i in tsp.result])
		order = [name_node[spot_name] for spot_name in spots]
		timelist.append(time.time())
		print(f"ルート抽出:{timelist[-1]-timelist[-2]}秒")

		#ルート
		pre_route_tsp = [ox.shortest_path(G,s1,s2,weight='length', cpus=1) for s1,s2 in zip(order[:-1],order[1:])]
		# 出力された順番をもとにからノードを辿る
		route_tsp = shrink_route(list(itertools.chain.from_iterable(pre_route_tsp))) #平坦化
		edges_tsp = [(route_tsp[i],route_tsp[i+1],0) for i in range(len(route_tsp)-1)]
		passed_symbols = [spot for spot in order if spot in route_tsp]

		timelist.append(time.time())
		print(f"最短:{timelist[-1]-timelist[-2]}秒")

		# 可視化
		# Folium マップを作成し、縮尺（ズーム レベル）を設定
		# 最短経路を地図にプロット
		map = folium.Map(control_scale=True)
		# エッジだけを持つ部分グラフを取得
		route_G = G.edge_subgraph(edges_tsp)

		timelist.append(time.time())
		print(f"部分グラフ:{timelist[-1]-timelist[-2]}秒")

		# エッジのジオメトリ情報を含むGeoDataFrameを取得
		gdf_edges = ox.graph_to_gdfs(route_G, nodes=False)
		# geometry列の座標情報を修正
		gdf_edges['geometry'] = gdf_edges.apply(fix_coordinates, axis=1)
		timelist.append(time.time())
		print(f"gdf_edges:{timelist[-1]-timelist[-2]}秒")

		# ジオメトリ情報を地図に追加
		for _, row in gdf_edges.iterrows():
			folium.PolyLine(locations=row['geometry'].coords, weight=5, color='red').add_to(map)  # weightを設定

		# マーカーを追加
		j = 0
		for i, symbol in enumerate(passed_symbols):
			print(f"{i+1:03d}:{G.nodes[symbol]['name']}")
			# loc = [G.nodes[symbol]['y'], G.nodes[symbol]['x']]
			name_list = str2list_strings(G.nodes[symbol]['name'])
			for name in name_list:
				if name in spots:
					loc = name_coord[name]
					pop_name = f"{name}"
					j += 1
					folium.Marker(loc, popup=pop_name, icon=folium.Icon(color='red')).add_to(map)

		# 縮尺とズームを設定
		map.fit_bounds(map.get_bounds())
		map.zoom_start = 15

		timelist.append(time.time())
		print(f"地図編集:{timelist[-1]-timelist[-2]}秒")

		# 保存
		map_html_str = map._repr_html_()
		map_html_str = map_html_str.replace('padding-bottom:60%;', '').replace('height:0;', 'height:80vh;')
		# # 正規表現パターン
		# pattern = r'<iframe\b[^>]*>(.*?)</iframe>'

		# # 正規表現検索
		# iframe_content = re.search(pattern, map_html_str, re.DOTALL)
		# # 結果の表示
		# if iframe_content:
		# 	map_html_str = iframe_content.group(0)
		# 	print(map_html_str)  # <iframe>タグから</iframe>タグまでの文字列全体
		# else:
		# 	print("一致する<iframe>タグが見つかりません")
		# 	break

		# map_html_index = map_html.replace('.html',f'_{route_index+1}.html')
		# MAP_PATH = os.path.join(d_settings.STATIC_ROOT, map_html_index)
		# map.save(MAP_PATH)
		# # HTMLの文字列データを取得
		# map_html_str = map._repr_html_()
		# timelist.append(time.time())
		# print(f"mapを保存:{timelist[-1]-timelist[-2]}秒")

		# # デバッグのためのスクリプト
		# print("デバッグ2")
		# if os.path.exists(MAP_PATH):
		# 	print(f"mapを保存しました:{MAP_PATH}")
		# 	# MAP_FOLDERの内容を表示
		# 	map_folder_contents = os.listdir(d_settings.STATIC_ROOT)
		# 	print("MAP_FOLDERの内容:")
		# 	for item in map_folder_contents:
		# 		print(item)
		# else:
		# 	raise FileNotFoundError(f"MAP_PATHが存在しませんでした:{MAP_PATH}")


		# 距離と所要時間を計算
		dist = int(tsp.cost(tsp.result))
		time_rq = int(tsp.cost(tsp.result) / 80.0) # 80m/minで計算
		if len(spots) > 2:
			via_spots = spots[1:-1]
		else:
			via_spots = []

		info_json = {
			"order":spots,
			"map_html_str":map_html_str,
			"distance":dist,
			"time":time_rq,
			"via_spots":via_spots,
				}
		info_json_list.append(info_json)
		timelist.append(time.time())
		print(f"info_json生成:{timelist[-1]-timelist[-2]}秒")
	
	# distanceが小さい順に並び替え
	info_json_list = sorted(info_json_list, key=lambda x: x["distance"])
	for idx, info_json in enumerate(info_json_list):
		info_json_list[idx]["name"] = f"経路{idx+1}"
	info_json_list_shrinked = [{key:val for key,val in info_json.items() if key != "map_html_str"} for info_json in info_json_list]
	print(f"info_json_list:{info_json_list_shrinked}")
	return info_json_list

if __name__ == "__main__":

	info_json_list = tsp_execute(
							  node_df=node_df,
							  spot_info_df=spot_info_df,
							  index_name=index_name,
							  index_tags=index_tags,
							  count_tags=count_tags,
							  start_name=start_name,
							  goal_name=goal_name,
							  aim_tags=aim_tags)
	