
import google.generativeai as genai
genai.configure(api_key="AIzaSyB9jIj4iMxBb79GOIpH8tjsh8g0QhknM98")

model = genai.GenerativeModel("gemini-1.5-pro")
response = model.generate_content("Explain how transformers work.")
print(response.text)
