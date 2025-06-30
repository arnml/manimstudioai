import requests
import json

url = "http://localhost:8000/render-code"
data = {
    "code": "from manim import *\n\nclass HelloWorld(Scene):\n    def construct(self):\n        text = Text(\"Hello, World!\")\n        self.play(Write(text))"
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, data=json.dumps(data), headers=headers)

print(response.status_code)
print(response.json())
