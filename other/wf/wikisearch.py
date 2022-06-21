import requests, difflib

URL = "https://api.warframestat.us/items"

r = requests.get(URL).json()

item_list = {x["name"]: x for x in r if "name" in x}



