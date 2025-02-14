import streamlit as st
from docx import Document
import requests
import os

def correct_text(text):
    api_key = st.secrets["DASHSCOPE_API_KEY"]
    url = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = f"Correct the following text for spelling, grammar, and punctuation errors without altering the meaning or format: {text}"
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
        corrected_text = response.json()["choices"][0]["message"]["content"]
        return corrected_text.strip()
    else:
        st.error(f"Error in correction: {response.text}")
        return None

def process_document(doc_path):
    try:
        doc = Document(doc_path)
        paragraphs = []
        for para in doc.paragraphs:
            paragraphs.append(para)
        return paragraphs, doc
    except Exception as e:
        st.error(f"Error processing the document: {e}")
        return None, None

def save_corrected_document(doc, corrected_paragraphs, output_path):
    try:
        for i, para in enumerate(doc.paragraphs):
            if i < len(corrected_paragraphs):
                para.text = corrected_paragraphs[i]
        doc.save(output_path)
    except Exception as e:
        st.error(f"Error saving the corrected document: {e}")

st.set_page_config(page_title="Text Correction Tool", page_icon="📝")
st.title("Spelling, Grammar, and Punctuation Corrector 📝")

uploaded_file = st.file_uploader("Upload a Word document (.docx) for correction", type=["docx"])

if uploaded_file is not None:
    if uploaded_file.size == 0:
        st.error("The uploaded file is empty. Please upload a valid .docx file.")
        st.stop()

    temp_input_path = "temp_input.docx"
    try:
        with open(temp_input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        st.error(f"Error saving the uploaded file: {e}")
        st.stop()

    paragraphs, doc = process_document(temp_input_path)

    if paragraphs is None or doc is None:
        st.error("The document could not be processed. Please ensure the file is a valid .docx document.")
        st.stop()

    if st.button("Correct Document"):
        total_paragraphs = len(paragraphs)
        progress_bar = st.progress(0)
        corrected_paragraphs = []

        st.info("Correcting spelling, grammar, and punctuation...")
        for i, para in enumerate(paragraphs):
            if para.text.strip() == "":
                corrected_paragraphs.append(para.text)  # Preserve empty paragraphs
                progress = (i + 1) / total_paragraphs
                progress_bar.progress(progress, text=f"Progress: {int(progress * 100)}%")
                continue

            corrected_text = correct_text(para.text)
            if corrected_text:
                corrected_paragraphs.append(corrected_text)
                progress = (i + 1) / total_paragraphs
                progress_bar.progress(progress, text=f"Progress: {int(progress * 100)}%")
            else:
                corrected_paragraphs.append(para.text)  # Preserve original text if correction fails

        if len(corrected_paragraphs) == total_paragraphs:
            st.success("Correction completed.")

            temp_output_path = "corrected_output.docx"
            save_corrected_document(doc, corrected_paragraphs, temp_output_path)

            # Verify that the corrected file exists before allowing download
            if os.path.exists(temp_output_path):
                try:
                    with open(temp_output_path, "rb") as f:
                        st.download_button(
                            label="Download Corrected Document",
                            data=f,
                            file_name="corrected_output.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                except Exception as e:
                    st.error(f"Error preparing the corrected document for download: {e}")
            else:
                st.error("The corrected document could not be generated. Please try again.")

            # Clean up temporary files
            try:
                os.remove(temp_input_path)
                if os.path.exists(temp_output_path):
                    os.remove(temp_output_path)
            except Exception as e:
                st.warning(f"Could not clean up temporary files: {e}")
else:
    st.warning("Please upload a Word document (.docx) to proceed.")
