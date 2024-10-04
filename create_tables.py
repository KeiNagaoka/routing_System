import os
import django

# Djangoの設定を環境変数から取得
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "routingSystem.settings")  # プロジェクト名に変更
django.setup()

from routing.models import Spot  # アプリ名を適切に変更してください
from routingSystem.backend.data_management import get_spot_info
from routingSystem.backend.core.utils import str2list_strings


def add_spots():
    spot_info = get_spot_info()
    
    for idx, spot_data in spot_info.iterrows():
        spot = Spot(
            name = spot_data["name"],
            latitude = spot_data["lat"],
            longitude = spot_data["lon"],
            tags = str2list_strings(spot_data["tags"]),
            hp = spot_data["hp"],
        )
        spot.save()

if __name__ == "__main__":
    add_spots()
    print("spots added successfully.")
