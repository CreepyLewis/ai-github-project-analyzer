# -----------------------------
# AI GitHub Project Analyzer - Ultimate Version
# -----------------------------
import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
import markdown2
import re
from graphviz import Digraph

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
# GITHUB API HELPERS WITH PAT SUPPORT
# -----------------------------
def get_github_headers():
    token = st.secrets.get("GITHUB_TOKEN")
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def parse_repo_url(url):
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if match:
        return match.group(1), match.group(2)
    else:
        st.error("Invalid GitHub repository URL")
        st.stop()

def get_repo_info(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url, headers=get_github_headers())
    return response.json()

def get_repo_files(owner, repo, path=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?per_page=100"
    response = requests.get(url, headers=get_github_headers())
    return response.json()

def get_readme(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(url, headers=get_github_headers())
    if response.status_code == 200:
        data = response.json()
        return base64.b64decode(data["content"]).decode("utf-8")
    return None

def get_languages(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    response = requests.get(url, headers=get_github_headers())
    return response.json() if response.status_code == 200 else {}

def get_contributors(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    response = requests.get(url, headers=get_github_headers())
    return response.json() if response.status_code == 200 else []

# -----------------------------
# GROQ API (or OpenAI) FUNCTIONS
# -----------------------------
if "GROQ_API_KEY" not in st.secrets:
    st.error("Groq API key missing. Add GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

from groq import Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def explain_repository(readme_text):
    prompt = f"Summarize this GitHub project in a few sentences and explain its purpose:\n\n{readme_text}"
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        return response.choices[0].message.content.strip()
    except:
        return "AI could not generate a response."

def explain_file(file_content, file_name):
    prompt = f"Explain this Python file {file_name} line by line in simple terms:\n\n{file_content}"
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        return response.choices[0].message.content.strip()
    except:
        return "AI could not generate a response."

def collect_repo_code(files):
    repo_text = ""
    for f in files:
        if f["type"] == "file" and f.get("download_url"):
            try:
                content = requests.get(f["download_url"]).text
                if len(content.strip()) == 0:
                    continue
                repo_text += f"\n\nFILE: {f['name']}\n"
                repo_text += content[:4000]
            except Exception as e:
                print(f"Failed to load {f['name']}: {e}")
    if len(repo_text.strip()) == 0:
        repo_text = "No code found in repository."
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
    try:
        return response.choices[0].message.content.strip()
    except:
        return "AI could not generate a response."

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
# REPO VISUALIZATION
# -----------------------------
def build_repo_graph_recursive_styled(owner, repo, parent="root", dot=None, path="", max_files_per_folder=20):
    if dot is None:
        dot = Digraph(comment='Repository Structure', format='svg')
        dot.attr('node', shape='folder', style='filled', color='#0d6efd')
        dot.node('root', 'ROOT', shape='folder', style='filled', color='#0d6efd')

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        contents = requests.get(url, headers=get_github_headers()).json()
    except Exception as e:
        print(f"Failed to fetch {path}: {e}")
        return dot

    files_count = 0
    for item in contents:
        node_name = f"{path}/{item['name']}" if path else item['name']
        if item["type"] == "dir":
            dot.node(node_name, f"📁 {item['name']}", shape='folder', style='filled', color='#0d6efd')
            dot.edge(parent, node_name)
            build_repo_graph_recursive_styled(owner, repo, parent=node_name, dot=dot, path=node_name, max_files_per_folder=max_files_per_folder)
        elif item["type"] == "file":
            ext = item["name"].split(".")[-1].lower()
            color_map = {
                "py": "#f0db4f",
                "js": "#f7df1e",
                "ts": "#007acc",
                "md": "#00ff41",
                "json": "#ff6f61",
            }
            color = color_map.get(ext, "#ffffff")
            dot.node(node_name, f"📄 {item['name']}", shape='note', style='filled', color=color)
            dot.edge(parent, node_name)
            files_count += 1

        if files_count >= max_files_per_folder:
            dot.node(f"{node_name}_more", f"📁 ... {len(contents) - files_count} more files", shape='folder', style='dashed', color='#6c757d')
            dot.edge(parent, f"{node_name}_more")
            break

    return dot

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
        st.error(f"Repository not found or API limit reached: {repo_info.get('message')}")
        st.stop()

    st.success("Repository analyzed successfully!")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Overview", "📂 Files", "📘 README", "💬 AI Chat", "🖼 Repo Visualization"]
    )

    # -----------------------------
    # OVERVIEW
    # -----------------------------
    with tab1:
        st.subheader("📊 Repository Overview")
        col1, col2, col3 = st.columns(3)
        col1.metric("⭐ Stars", repo_info.get("stargazers_count",0))
        col2.metric("🍴 Forks", repo_info.get("forks_count",0))
        col3.metric("🐛 Issues", repo_info.get("open_issues_count",0))
        col4, col5, col6 = st.columns(3)
        col4.metric("👀 Watchers", repo_info.get("watchers_count",0))
        col5.metric("📦 Size (KB)", repo_info.get("size",0))
        col6.metric("🧑‍💻 Default Branch", repo_info.get("default_branch","main"))
        st.markdown("---")
        st.write("**Repository Name:**", repo_info.get("name","N/A"))
        st.write("**Owner:**", repo_info.get("owner",{}).get("login","N/A"))
        st.write("**Description:**", repo_info.get("description",""))
        st.write("**Primary Language:**", repo_info.get("language","N/A"))
        st.write("**Created:**", repo_info.get("created_at","N/A"))
        st.write("**Last Updated:**", repo_info.get("updated_at","N/A"))
        st.markdown(f"[🔗 Open Repository]({repo_info.get('html_url','#')})")

        # Contributors
        contributors = get_contributors(owner, repo)
        st.subheader("🏆 Top Contributors")
        if isinstance(contributors, list) and len(contributors)>0:
            for c in contributors[:5]:
                st.write(f"{c.get('login','N/A')} — {c.get('contributions',0)} commits")
        else:
            st.write("No contributors found or API limit reached.")
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

        if "ai_answer" not in st.session_state:
            st.session_state.ai_answer = ""

        user_question = st.text_input("Ask anything about this repository", placeholder="How do I run this project?")

        if st.button("Ask AI"):
            if user_question:
                with st.spinner("AI analyzing repository..."):
                    st.session_state.ai_answer = chat_with_repo(user_question, repo_text)

        if st.session_state.ai_answer:
            st.markdown("### 🤖 AI Answer")
            st.write(st.session_state.ai_answer)

    # -----------------------------
    # REPO VISUALIZATION TAB
    # -----------------------------
    with tab5:
        st.subheader("🖼 Repository Structure Visualization (Styled)")

        try:
            repo_graph = build_repo_graph_recursive_styled(owner, repo)
            st.graphviz_chart(repo_graph)
        except Exception as e:
            st.error(f"Failed to generate repo graph: {e}")
