import streamlit as st
from docx import Document
import requests
import os

def translate_text(text, target_language):
    api_key = st.secrets["DASHSCOPE_API_KEY"]
    url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = f"Translate the following text to {target_language}: {text}"
    data = {
        "model": "qwen-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        translated_text = response.json()["choices"][0]["message"]["content"]
        return translated_text
    else:
        st.error(f"Error in translation: {response.text}")
        return None

def process_document(doc_path):
    doc = Document(doc_path)
    paragraphs = []
    for para in doc.paragraphs:
        paragraphs.append(para)
    return paragraphs, doc

def save_translated_document(doc, translated_paragraphs, output_path):
    for i, para in enumerate(doc.paragraphs):
        if i < len(translated_paragraphs):
            para.text = translated_paragraphs[i]
    doc.save(output_path)

st.set_page_config(page_title="Double Translation Tool", page_icon="🔄")
st.title("Double Translation Tool 🔄")

uploaded_file = st.file_uploader("Upload a Word document (.docx)", type=["docx"])

if uploaded_file is not None:
    temp_input_path = "temp_input.docx"
    with open(temp_input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    paragraphs, doc = process_document(temp_input_path)

    original_language = st.text_input("Enter the original language of the document (e.g., 'Spanish'):", value="Spanish")

    if st.button("Translate"):
        total_paragraphs = len(paragraphs)
        progress_bar = st.progress(0)
        translated_paragraphs = []

        st.info("Translating from original language to English...")
        for i, para in enumerate(paragraphs):
            english_translation = translate_text(para.text, "English")
            if english_translation:
                translated_paragraphs.append(english_translation)
                progress = (i + 1) / total_paragraphs
                progress_bar.progress(progress, text=f"Progress: {int(progress * 100)}%")

        if len(translated_paragraphs) == total_paragraphs:
            st.success("First translation (Original -> English) completed.")

            st.info("Translating back from English to the original language...")
            final_translated_paragraphs = []
            for i, para in enumerate(translated_paragraphs):
                final_translation = translate_text(para, original_language)
                if final_translation:
                    final_translated_paragraphs.append(final_translation)
                    progress = (i + 1) / total_paragraphs
                    progress_bar.progress(progress, text=f"Progress: {int(progress * 100)}%")

            if len(final_translated_paragraphs) == total_paragraphs:
                st.success("Second translation (English -> Original) completed.")

                temp_output_path = "translated_output.docx"
                save_translated_document(doc, final_translated_paragraphs, temp_output_path)

                with open(temp_output_path, "rb") as f:
                    st.download_button(
                        label="Download Translated Document",
                        data=f,
                        file_name="translated_output.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )

                os.remove(temp_input_path)
                os.remove(temp_output_path)
