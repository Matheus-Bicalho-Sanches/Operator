import requests

API_KEY = "AIzaSyATqElu9BHWivL3XclWwSDikImSWerKO5E"
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

response = requests.get(url)
print(response.json())