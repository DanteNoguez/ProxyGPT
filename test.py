import requests

url = "https://f7d1-177-248-18-94.ngrok-free.app/test?name=dad"
headers = {'accept': 'application/json'}
data = {"dummy_key": "dummy_value"}

response = requests.post(url, headers=headers, json=data)

print(response.json())
