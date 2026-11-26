import os, datetime
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_data(category):
    if not isinstance(category, str):
        raise TypeError("Passed category must be a string")
    category = category.lower().strip().capitalize()
    return os.listdir(PROJECT_ROOT / "Data" / category)

def delete_old_assets(category, amount_keeping, keep_newest = True):
    assets: list[str] = get_data(category)
    sorted_assets = []
    for asset in assets:
        asset = asset.split(".")[0]
        try:
            asset = datetime.datetime.fromisoformat(asset)
        except:
            pass
        sorted_assets.append(asset)
    sorted_assets.sort(reverse=keep_newest)
    sorted_assets = sorted_assets[:amount_keeping]
    for asset in assets:
        if asset.split(".")[0] not in sorted_assets:
            os.remove(PROJECT_ROOT / "Data" / category / asset)
    return
        
    

