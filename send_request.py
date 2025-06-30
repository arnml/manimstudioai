import requests
import json

url = "https://manim-studio-backend-952720044146.us-central1.run.app/generate"
payload = {"prompt": "Create a simple animation of a square"}
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()  # Raise an exception for bad status codes
    print(response.json())
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
    print("Response body:", response.text if 'response' in locals() else 'No response')