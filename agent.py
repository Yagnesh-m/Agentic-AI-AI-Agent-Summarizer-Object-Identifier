import os
import io
import base64
import tempfile
from pdf2image import convert_from_path
import requests
from PIL import Image
from langdetect import detect
import google.generativeai as genai

POPPLER_PATH = r"C:\Users\yagne\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin"
API_KEY = "AIzaSyBY0KKWo8tzik7GuYl1h5zc-RgGes52cVI"  # Replace with your valid Google API key


def ocr_google_vision(path, api_key):
    with open(path, "rb") as img_file:
        content = img_file.read()

    image_base64 = base64.b64encode(content).decode("utf-8")

    url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "requests": [{
            "image": {"content": image_base64},
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]
        }]
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        result = response.json()
        text = result['responses'][0].get('fullTextAnnotation', {}).get('text', '')
        return text
    else:
        print(f"❌ Google Vision API Error: {response.status_code} - {response.text}")
        return ""


def extract_text_from_pdf(pdf_path, poppler_path, api_key):
    print("🖼️ Converting PDF pages to images...")
    try:
        pages = convert_from_path(pdf_path, poppler_path=poppler_path)
    except Exception as e:
        print(f"❌ Error during PDF to image conversion: {e}")
        return ""

    full_text = ""

    for i, page in enumerate(pages):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
            temp_img_path = temp_img.name
            page.save(temp_img_path, "PNG")

        print(f"🔍 Extracting text from Page {i + 1}...")
        page_text = ocr_google_vision(temp_img_path, api_key)

        if page_text.strip():
            full_text += f"\n--- Page {i+1} ---\n{page_text.strip()}"
        else:
            print(f"⚠️ No text found on Page {i + 1}")

        try:
            os.remove(temp_img_path)
        except Exception as e:
            print(f"⚠️ Could not delete temp file: {e}")

    return full_text.strip()


def detect_language(text):
    try:
        return detect(text)
    except Exception:
        return "Unknown"


def gpt_summarize_google(text, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest")  # Updated: no version prefix
        prompt = f"Summarize the following document in 5-6 sentences:\n\n{text[:4000]}"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error during GPT summarization: {e}")
        return "Summarization failed."


def main():
    print("📁 Google Vision + Gemini PDF OCR Tool")
    pdf_path = input("📄 Enter path to PDF file: ").strip()

    if not os.path.exists(pdf_path):
        print("❌ File not found. Please check the path.")
        return

    if not API_KEY:
        print("❌ Google API key not set. Please set it in the script.")
        return

    print("🧠 Extracting text using Google Vision API...")
    extracted_text = extract_text_from_pdf(pdf_path, POPPLER_PATH, API_KEY)

    if extracted_text:
        print("\n🧾 Extracted Text:")
        print(extracted_text[:1000] + "\n...")  # Show first 1000 chars

        lang = detect_language(extracted_text)
        print(f"\n🌐 Detected Language: {lang}")

        print("\n🤖 GPT-Based Summary (Gemini-Pro):")
        summary = gpt_summarize_google(extracted_text, API_KEY)
        print(summary)

        # Save extracted text
        save_path = pdf_path.replace(".pdf", "_extracted.txt")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        print(f"\n💾 Text saved to: {save_path}")
    else:
        print("❌ No text extracted. Try a clearer PDF.")


if __name__ == "__main__":
    main()
