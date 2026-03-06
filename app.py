import streamlit as st
import requests

st.title("🤖 AI GitHub Project Analyzer")

repo_url = st.text_input("Paste GitHub Repository URL")

if st.button("Analyze"):

    owner = repo_url.split("/")[-2]
    repo = repo_url.split("/")[-1]

    api = f"https://api.github.com/repos/{owner}/{repo}"
    data = requests.get(api).json()

    st.subheader("Repository Info")
    st.write("Name:", data["name"])
    st.write("Stars:", data["stargazers_count"])
    st.write("Forks:", data["forks_count"])
    st.write("Language:", data["language"])
