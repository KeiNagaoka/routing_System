import pandas as pd
from sqlalchemy import create_engine
import os
import django
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'routingSystem.settings')  # 'routingSystem.settings'をプロジェクト名に置き換えてください
django.setup()
from models import MyTable  # モデルをインポート

# Django設定からSQLiteのデータベースに接続するエンジンを作成
engine = create_engine('sqlite:///db.sqlite3')

# DataFrameの内容をデータベースに保存する関数
def save_df_to_sql(df, table_name):
    df.to_sql(table_name, con=engine, if_exists='append', index=False)

if __name__=="__main__":
    # 例: DataFrameを作成
    data = {
        'column1': ['value1', 'value2'],
        'column2': [10, 20],
    }
    df = pd.DataFrame(data)

    # データをデータベースのテーブルに保存
    save_df_to_sql(df, 'my_table')

    # テーブルから全てのデータを取得
    data = MyTable.objects.all()

    # データを表示
    for item in data:
        print(item.column1, item.column2)