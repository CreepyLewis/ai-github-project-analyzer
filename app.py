# -----------------------------
# AI GitHub Project Analyzer - Ultimate Version
# -----------------------------

import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
import markdown2
import re
from groq import Groq

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
# GROQ API SETUP
# -----------------------------
if "GROQ_API_KEY" not in st.secrets:
    st.error("Groq API key missing. Add GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# -----------------------------
# FUNCTIONS
# -----------------------------
def parse_repo_url(url):
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if match:
        return match.group(1), match.group(2)
    else:
        st.error("Invalid GitHub repository URL")
        st.stop()

def get_repo_info(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    return requests.get(url).json()

def get_repo_files(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents?per_page=100"
    return requests.get(url).json()

def get_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return base64.b64decode(data["content"]).decode("utf-8")
    return None

# -----------------------------
# AI FUNCTIONS
# -----------------------------
def explain_repository(readme_text):
    prompt = f"Summarize this GitHub project in a few sentences and explain its purpose:\n\n{readme_text}"
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def explain_file(file_content, file_name):
    prompt = f"Explain this Python file {file_name} line by line in simple terms:\n\n{file_content}"
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

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
# Additional Features
# -----------------------------
def build_tree(files):
    tree = ""
    for f in files:
        tree += f"📄 {f['name']}\n"
    return tree

def get_languages(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    return requests.get(url).json()

def get_contributors(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    return requests.get(url).json()

def improve_readme(readme_text):
    prompt = f"Analyze this GitHub README and suggest improvements:\n\n{readme_text}"
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message.content

def collect_repo_code(files):
    repo_text = ""
    for f in files:
        if f["type"] == "file" and f.get("download_url"):
            try:
                content = requests.get(f["download_url"]).text
                repo_text += f"\n\nFILE: {f['name']}\n"
                repo_text += content[:4000]  # limit length
            except:
                pass
    return repo_text

def chat_with_repo(question, repo_text):
    prompt = f"""
You are an AI software engineer.
Answer the question using the repository code below.

REPOSITORY CODE:
{repo_text}

QUESTION:
{question}
"""
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message.content

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
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Overview", "📂 Files", "📘 README", "💬 AI Chat"]
    )

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

        # Repository Health Score
        st.markdown("---")
        st.subheader("💚 Repository Health")
        health = 0
        if repo_info["stargazers_count"] > 10: health += 20
        if repo_info["forks_count"] > 5: health += 20
        if readme: health += 30
        if repo_info["description"]: health += 10
        if repo_info["open_issues_count"] < 10: health += 20
        st.progress(health/100)
        st.write(f"Health Score: **{health}/100**")

        # Languages
        st.subheader("🧠 Languages Used")
        languages = get_languages(owner, repo)
        for lang, size in languages.items():
            st.write(f"**{lang}** — {size} bytes")

        # Contributors
        st.subheader("🏆 Top Contributors")
        contributors = get_contributors(owner, repo)
        for c in contributors[:5]:
            st.write(f"{c['login']} — {c['contributions']} commits")

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
            # Repository Structure Tree
            st.markdown("### 🏗 Repository Structure")
            tree = build_tree(files)
            st.code(tree)
        else:
            st.error("Could not fetch repository files")

    # -----------------------------
    # README TAB
    # -----------------------------
    with tab3:
        st.subheader("📘 README Preview (GitHub-style)")
        if readme:
            html_readme = markdown2.markdown(readme, extras=["fenced-code-blocks","tables","strike","target-blank-links"])
            custom_css = """
            <style>
            .readme-container { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial; background-color:#0d0d0d; color:#00ff41; padding:20px; border-radius:10px; }
            .readme-container table {border-collapse:collapse;width:100%;}
            .readme-container table,th,td {border:1px solid #00ff41;}
            .readme-container th,td {padding:8px;text-align:left;}
            .readme-container code {background:#111;color:#ffdd00;padding:2px 4px;border-radius:4px;}
            .readme-container pre {background:#111;padding:10px;border-radius:6px;overflow-x:auto;}
            .readme-container img {max-width:100%;}
            </style>
            """
            components.html(f"{custom_css}<div class='readme-container'>{html_readme}</div>", height=1000, scrolling=True)
            if st.button("🧠 Summarize Project with AI"):
                with st.spinner("Generating AI summary..."):
                    summary = explain_repository(readme)
                    st.markdown("**AI Project Summary:**")
                    st.write(summary)
            if st.button("🚀 Suggest README Improvements"):
                with st.spinner("Analyzing README..."):
                    improvements = improve_readme(readme)
                    st.write(improvements)
            # Contribution Snake
            snake_url = f"https://raw.githubusercontent.com/{owner}/{repo}/output/snake-dark.svg"
            st.image(snake_url, use_container_width=True)
            # Activity Graph
            graph_url = f"https://github-readme-activity-graph.vercel.app/graph?username={owner}&theme=github-compact&area=true&hide_border=true"
            st.image(graph_url, use_container_width=True)
            github_readme_url = f"https://github.com/{owner}/{repo}#readme"
            st.markdown(f"[📖 View Full README on GitHub]({github_readme_url})")
            # Social Links
            default_socials = {
                "GitHub":"https://github.com/CreepyLewis",
                "LinkedIn":"https://linkedin.com/in/lewis-kithome",
                "Twitter":"https://twitter.com/your_twitter",
                "Instagram":"https://instagram.com/lewis.karl7",
                "TikTok":"https://tiktok.com/@lewis.karl7",
                "YouTube":"https://youtube.com/@LEWISKITHOME-I9y",
                "Spotify":"https://open.spotify.com/user/creepylewis"
            }
            socials_found = extract_social_links(readme)
            socials_found = {**default_socials, **socials_found}
            if socials_found:
                st.markdown("---")
                st.subheader("🌐 Social Links")
                scroll_container = st.container()
                cols = scroll_container.columns(len(socials_found))
                icons = {
                    "GitHub":"https://cdn-icons-png.flaticon.com/512/25/25231.png",
                    "LinkedIn":"https://cdn-icons-png.flaticon.com/512/174/174857.png",
                    "Twitter":"https://cdn-icons-png.flaticon.com/512/733/733579.png",
                    "Instagram":"https://cdn-icons-png.flaticon.com/512/174/174855.png",
                    "TikTok":"https://cdn-icons-png.flaticon.com/512/3046/3046121.png",
                    "YouTube":"https://cdn-icons-png.flaticon.com/512/1384/1384060.png",
                    "Spotify":"https://cdn-icons-png.flaticon.com/512/174/174872.png"
                }
                for i,(platform,link) in enumerate(socials_found.items()):
                    cols[i].image(icons.get(platform), width=24)
                    cols[i].markdown(f"[{platform}]({link})")
        else:
            st.warning("No README found for this repository")

    # -----------------------------
    # AI CHAT TAB
    # -----------------------------
    with tab4:
        st.subheader("💬 Chat With This Repository")
        repo_text = collect_repo_code(files)
        user_question = st.text_input("Ask anything about this repository", placeholder="How do I run this project?")
        if st.button("Ask AI"):
            if user_question:
                with st.spinner("AI analyzing repository..."):
                    answer = chat_with_repo(user_question, repo_text)
                st.markdown("### 🤖 AI Answer")
                st.write(answer)
