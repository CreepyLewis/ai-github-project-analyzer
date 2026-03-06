import streamlit as st
import streamlit.components.v1 as components
import requests
import base64
import openai

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
# Set OPENAI_API_KEY in Streamlit Secrets
openai.api_key = st.secrets.get("OPENAI_API_KEY")

# -----------------------------
# FUNCTIONS
# -----------------------------

def parse_repo_url(url):
    """Extract owner and repo name from GitHub URL"""
    parts = url.strip("/").split("/")
    owner = parts[-2]
    repo = parts[-1]
    return owner, repo


def get_repo_info(owner, repo):
    """Fetch repository info from GitHub API"""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    response = requests.get(url)
    return response.json()


def get_repo_files(owner, repo):
    """Fetch files in repository"""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    response = requests.get(url)
    return response.json()


def get_readme(owner, repo):
    """Fetch README content"""
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
    else:
        return None


def explain_repository(readme_text):
    """Summarize the project using AI"""
    prompt = f"Summarize this GitHub project in a few sentences and explain its purpose:\n\n{readme_text}"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=200,
        temperature=0.5
    )
    return response.choices[0].text.strip()


def explain_file(file_content, file_name):
    """Explain code file using AI"""
    prompt = f"Explain this Python file {file_name} line by line in simple terms:\n\n{file_content}"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=400,
        temperature=0.5
    )
    return response.choices[0].text.strip()


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
    tab1, tab2, tab3 = st.tabs([
        "📊 Overview",
        "📂 Files",
        "📘 README"
    ])

    # -----------------------------
    # OVERVIEW TAB
    # -----------------------------
    with tab1:

        st.subheader("📊 Repository Overview")

        # Top metrics
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

            file_names = []
            file_map = {}

            for file in files:
                if file["type"] == "file":
                    file_names.append(file["name"])
                    file_map[file["name"]] = file["download_url"]

            st.write(f"Total files found: {len(file_names)}")

            selected_file = st.selectbox(
                "Select a file to view",
                file_names
            )

            if selected_file:
                file_url = file_map[selected_file]
                file_content = requests.get(file_url).text

                st.subheader("📄 File Content")
                st.code(file_content, language="python")

                # AI explanation
                if st.button(f"🧠 Explain {selected_file}"):
                    with st.spinner("Generating AI explanation..."):
                        explanation = explain_file(file_content, selected_file)
                        st.markdown("**AI Explanation:**")
                        st.write(explanation)

        else:
            st.error("Could not fetch repository files")

    # -----------------------------
    # README TAB (HTML + AI Summary)
    # -----------------------------
    with tab3:

        st.subheader("📘 README Documentation")

        if readme:
            # Render full HTML
            line_count = readme.count("\n")
            height = max(600, min(3000, line_count * 20))
            components.html(readme, height=height, scrolling=True)

            # AI Project Summary
            if st.button("🧠 Summarize Project with AI"):
                with st.spinner("Generating AI summary..."):
                    summary = explain_repository(readme)
                    st.markdown("**AI Project Summary:**")
                    st.write(summary)

        else:
            st.warning("No README found for this repository")
