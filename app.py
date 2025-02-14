import streamlit as st
from docx import Document
import requests
import os

# Función para traducir texto usando la API de Groq
def translate_text(text, target_language):
    api_key = st.secrets["GROQ_API_KEY"]
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    prompt = f"Translate the following text to {target_language}: {text}"
    data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a translation model."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": "llama3-70b-8192",
        "temperature": 0.33,
        "max_completion_tokens": 29900,
        "top_p": 1,
        "stream": True,
        "stop": None
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        # Extraer la respuesta traducida
        translated_text = response.json()["choices"][0]["message"]["content"]
        return translated_text
    else:
        st.error(f"Error in translation: {response.text}")
        return None

# Función para procesar el documento Word
def process_document(doc_path):
    doc = Document(doc_path)
    original_text = []
    for para in doc.paragraphs:
        original_text.append(para.text)
    return "\n".join(original_text), doc

# Función para guardar el documento traducido
def save_translated_document(doc, translated_text, output_path):
    paragraphs = translated_text.split("\n")
    for i, para in enumerate(doc.paragraphs):
        if i < len(paragraphs):
            para.text = paragraphs[i]
    doc.save(output_path)

# Configuración de la página de Streamlit
st.set_page_config(page_title="Double Translation App", page_icon="🔄")
st.title("Double Translation App 🔄")

# Subida del archivo Word
uploaded_file = st.file_uploader("Upload a Word document (.docx)", type=["docx"])
if uploaded_file is not None:
    # Guardar el archivo subido temporalmente
    temp_input_path = "temp_input.docx"
    with open(temp_input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Procesar el documento
    original_text, doc = process_document(temp_input_path)
    
    # Detectar el idioma original (asumiendo que el usuario lo proporciona)
    original_language = st.text_input("Enter the original language of the document (e.g., 'Spanish'):", value="Spanish")
    
    if st.button("Translate"):
        # Primera traducción: Idioma original -> Inglés
        st.info("Translating from original language to English...")
        english_translation = translate_text(original_text, "English")
        
        if english_translation:
            st.success("First translation (Original -> English) completed.")
            
            # Segunda traducción: Inglés -> Idioma original
            st.info("Translating back from English to the original language...")
            final_translation = translate_text(english_translation, original_language)
            
            if final_translation:
                st.success("Second translation (English -> Original) completed.")
                
                # Guardar el documento traducido
                temp_output_path = "translated_output.docx"
                save_translated_document(doc, final_translation, temp_output_path)
                
                # Permitir al usuario descargar el archivo traducido
                with open(temp_output_path, "rb") as f:
                    st.download_button(
                        label="Download Translated Document",
                        data=f,
                        file_name="translated_output.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                
                # Limpiar archivos temporales
                os.remove(temp_input_path)
                os.remove(temp_output_path)
