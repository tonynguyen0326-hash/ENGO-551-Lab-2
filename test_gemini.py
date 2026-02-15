import os
import requests

API_KEY = os.getenv("GEMINI_API_KEY")

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

headers = {
    "Content-Type": "application/json"
}

body = {
    "contents": [{
        "parts": [{
            "text": "Summarize this in under 20 words: Python is a powerful programming language used for web development, AI, and data science."
        }]
    }]
}

res = requests.post(
    url,
    params={"key": API_KEY},
    headers=headers,
    json=body
)

print(res.status_code)
print(res.json())