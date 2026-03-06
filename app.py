import streamlit as st
import requests
import base64

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
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
    else:
        return None


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

        st.subheader("Repository Overview")

        col1, col2, col3 = st.columns(3)

        col1.metric("⭐ Stars", repo_info["stargazers_count"])
        col2.metric("🍴 Forks", repo_info["forks_count"])
        col3.metric("🐛 Issues", repo_info["open_issues_count"])

        st.write("**Repository Name:**", repo_info["name"])
        st.write("**Description:**", repo_info["description"])
        st.write("**Language:**", repo_info["language"])

    # -----------------------------
    # FILES TAB
    # -----------------------------

    with tab2:

        st.subheader("Project Files")

        if isinstance(files, list):

            for file in files:

                if file["type"] == "dir":
                    st.write("📁", file["name"])
                else:
                    st.write("📄", file["name"])

        else:
            st.error("Could not fetch repository files")

    # -----------------------------
    # README TAB
    # -----------------------------

    with tab3:

        st.subheader("README Documentation")

        if readme:
            st.markdown(readme)
        else:
            st.warning("No README found for this repository")
