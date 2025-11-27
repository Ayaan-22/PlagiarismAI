import streamlit as st
import requests

API_URL = "http://127.0.0.1:9001/check"

st.title("🧠 AI Plagiarism Checker")
st.write("Upload a PDF or enter text below to check for plagiarism.")

# Inputs
uploaded_file = st.file_uploader("Upload PDF", type="pdf")
text_input = st.text_area("Or paste text here", height=200)

if st.button("Check Plagiarism"):
    
    with st.spinner("Checking... Please wait"):
        
        data = {}
        files = {}

        if text_input:
            data["text"] = text_input
        
        if uploaded_file:
            files["file"] = (uploaded_file.name, uploaded_file, "application/pdf")

        response = requests.post(API_URL, data=data, files=files)

        if response.status_code != 200:
            st.error("Error processing request")
        else:
            result = response.json()
            st.subheader(f"🔍 Plagiarism Score: **{result['plagiarism_percent']}%**")

            st.write("---")
            st.subheader("Matched Sources")

            for m in result["matches"]:
                st.write(f"**Similarity:** {m['similarity']}%")
                st.write(f"**Matched text:** {m['chunk']}...")
                st.write(f"**Source:** {m['source']}")
                st.write("---")
