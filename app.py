# -----------------------------
# AI GitHub Project Analyzer
# -----------------------------

import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
import openai
import markdown2
import re

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="AI GitHub Project Analyzer",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI GitHub Project Analyzer")

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("Repository Input")
repo_url = st.sidebar.text_input(
    "Paste GitHub Repository URL",
    placeholder="https://github.com/user/repo"
)
analyze = st.sidebar.button("Analyze Repository")

# -----------------------------
# OPENAI API SETUP
# -----------------------------
openai.api_key = st.secrets.get("OPENAI_API_KEY")

# -----------------------------
# FUNCTIONS
# -----------------------------
def parse_repo_url(url):
    parts = url.strip("/").split("/")
    owner = parts[-2]
    repo = parts[-1]
    return owner, repo

def get_repo_info(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url)
    return response.json()

def get_repo_files(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    response = requests.get(url)
    return response.json()

def get_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return base64.b64decode(data["content"]).decode("utf-8")
    return None

def explain_repository(readme_text):
    prompt = f"Summarize this GitHub project in a few sentences and explain its purpose:\n\n{readme_text}"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=200,
        temperature=0.5
    )
    return response.choices[0].text.strip()

def explain_file(file_content, file_name):
    prompt = f"Explain this Python file {file_name} line by line in simple terms:\n\n{file_content}"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=400,
        temperature=0.5
    )
    return response.choices[0].text.strip()

# Function to extract social links from README
def extract_social_links(readme_text):
    social_platforms = {
        "GitHub": r"https?://github\.com/[\w\-]+",
        "LinkedIn": r"https?://linkedin\.com/in/[\w\-]+",
        "Twitter": r"https?://twitter\.com/[\w\-]+",
        "Instagram": r"https?://instagram\.com/[\w\.\-]+",
        "TikTok": r"https?://tiktok\.com/@[\w\.\-]+",
        "YouTube": r"https?://(www\.)?youtube\.com/[\w\-\?=]+",
        "Spotify": r"https?://open\.spotify\.com/user/[\w\.\-]+"
    }
    found = {}
    for name, pattern in social_platforms.items():
        match = re.search(pattern, readme_text)
        if match:
            found[name] = match.group(0)
    return found

# -----------------------------
# MAIN ANALYSIS
# -----------------------------
if analyze:
    if repo_url == "":
        st.warning("Please enter a repository URL")
        st.stop()

    owner, repo = parse_repo_url(repo_url)

    with st.spinner("Analyzing repository..."):
        repo_info = get_repo_info(owner, repo)
        files = get_repo_files(owner, repo)
        readme = get_readme(owner, repo)

    if "message" in repo_info:
        st.error("Repository not found or API limit reached")
        st.stop()

    st.success("Repository analyzed successfully!")

    # -----------------------------
    # TABS
    # -----------------------------
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📂 Files", "📘 README"])

    # -----------------------------
    # OVERVIEW TAB
    # -----------------------------
    with tab1:
        st.subheader("📊 Repository Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("⭐ Stars", repo_info["stargazers_count"])
        col2.metric("🍴 Forks", repo_info["forks_count"])
        col3.metric("🐛 Issues", repo_info["open_issues_count"])
        col4, col5, col6 = st.columns(3)
        col4.metric("👀 Watchers", repo_info["watchers_count"])
        col5.metric("📦 Size (KB)", repo_info["size"])
        col6.metric("🧑‍💻 Default Branch", repo_info["default_branch"])
        st.markdown("---")
        st.write("**Repository Name:**", repo_info["name"])
        st.write("**Owner:**", repo_info["owner"]["login"])
        st.write("**Description:**", repo_info["description"])
        st.write("**Primary Language:**", repo_info["language"])
        st.write("**Created:**", repo_info["created_at"])
        st.write("**Last Updated:**", repo_info["updated_at"])
        st.markdown(f"[🔗 Open Repository]({repo_info['html_url']})")

    # -----------------------------
    # FILES TAB
    # -----------------------------
    with tab2:
        st.subheader("📂 Project Files")
        if isinstance(files, list):
            file_names = [f["name"] for f in files if f["type"]=="file"]
            file_map = {f["name"]:f["download_url"] for f in files if f["type"]=="file"}
            st.write(f"Total files found: {len(file_names)}")
            selected_file = st.selectbox("Select a file to view", file_names)
            if selected_file:
                file_content = requests.get(file_map[selected_file]).text
                st.subheader("📄 File Content")
                st.code(file_content, language="python")
                if st.button(f"🧠 Explain {selected_file}"):
                    with st.spinner("Generating AI explanation..."):
                        explanation = explain_file(file_content, selected_file)
                        st.markdown("**AI Explanation:**")
                        st.write(explanation)
        else:
            st.error("Could not fetch repository files")

    # -----------------------------
    # README TAB
    # -----------------------------
    with tab3:
        st.subheader("📘 README Preview (GitHub-style)")

        if readme:
            # Convert Markdown to HTML
            html_readme = markdown2.markdown(readme, extras=["fenced-code-blocks", "tables", "strike", "target-blank-links"])

            # Custom CSS for GitHub-like dark matrix style
            custom_css = """
            <style>
            .readme-container {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
                background-color: #0d0d0d;
                color: #00ff41;
                padding: 20px;
                border-radius: 10px;
            }
            .readme-container table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 15px;
            }
            .readme-container table, .readme-container th, .readme-container td {
                border: 1px solid #00ff41;
            }
            .readme-container th, .readme-container td {
                padding: 8px;
                text-align: left;
            }
            .readme-container a {
                color: #00ff41;
                text-decoration: underline;
            }
            .readme-container code {
                background-color: #111;
                padding: 2px 4px;
                border-radius: 4px;
                color: #ffdd00;
            }
            .readme-container pre {
                background-color: #111;
                padding: 10px;
                border-radius: 6px;
                overflow-x: auto;
            }
            .readme-container img {
                max-width: 100%;
            }
            </style>
            """

            # Render README preview
            components.html(f"{custom_css}<div class='readme-container'>{html_readme}</div>", height=1000, scrolling=True)

            # AI Project Summary
            if st.button("🧠 Summarize Project with AI"):
                with st.spinner("Generating AI summary..."):
                    summary = explain_repository(readme)
                    st.markdown("**AI Project Summary:**")
                    st.write(summary)

            # Contribution Snake
            snake_url = f"https://raw.githubusercontent.com/{owner}/{repo}/output/snake-dark.svg"
            st.image(snake_url, use_column_width=True)

            # Activity Graph
            graph_url = f"https://github-readme-activity-graph.vercel.app/graph?username={owner}&theme=github-compact&area=true&hide_border=true"
            st.image(graph_url, use_column_width=True)

            # Full GitHub README link
            github_readme_url = f"https://github.com/{owner}/{repo}#readme"
            st.markdown(f"[📖 View Full README on GitHub]({github_readme_url})", unsafe_allow_html=True)

            # -----------------------------
            # DYNAMIC SOCIAL LINKS
            # -----------------------------
            socials = extract_social_links(readme)
            if socials:
                st.markdown("---")
                st.subheader("🌐 Social Links Found")
                cols = st.columns(len(socials))
                icons = {
                    "GitHub": "https://cdn-icons-png.flaticon.com/512/25/25231.png",
                    "LinkedIn": "https://cdn-icons-png.flaticon.com/512/174/174857.png",
                    "Twitter": "https://cdn-icons-png.flaticon.com/512/733/733579.png",
                    "Instagram": "https://cdn-icons-png.flaticon.com/512/174/174855.png",
                    "TikTok": "https://cdn-icons-png.flaticon.com/512/3046/3046121.png",
                    "YouTube": "https://cdn-icons-png.flaticon.com/512/1384/1384060.png",
                    "Spotify": "https://cdn-icons-png.flaticon.com/512/174/174872.png"
                }
                for i, (platform, link) in enumerate(socials.items()):
                    cols[i].image(icons.get(platform), width=24)
                    cols[i].markdown(f"[{platform}]({link})")
            else:
                st.info("No social links detected in this README")
        else:
            st.warning("No README found for this repository")
