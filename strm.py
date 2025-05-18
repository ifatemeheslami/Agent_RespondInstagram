import streamlit as st
import instaloader
import openai
import time
from typing import List, Tuple


# Set openai API key from st.secrets or fallback:
openai.api_key = st.secrets["openai_api_key"] if "openai_api_key" in st.secrets else "YOUR_OPENAI_API_KEY"


st.set_page_config(page_title = "Instagram comment replier", layout = "centered")
st.title("Instagram comment replier with GPT-4")
st.write("Automatically generate polite, helpful replies to your Instagram post comments using GPT-4.")


# Sidebar for credentials and input
st.sidebar.header("Instagram Login")
username = st.sidebar.text_input("Instagram Username", value="", max_chars=50)
password = st.sidebar.text_input("Instagram Password", value="", type="password", max_chars=50)
st.sidebar.header("Post Details")
shortcode = st.sidebar.text_input("Instagram Post Shortcode", value="", max_chars=100, help="The unique code in the post URL, e.g. https://instagram.com/p/**shortcode**/")


submit = st.sidebar.button("Fetch & Reply to Comments")


# Helper: Fetch comments from a post by shortcode
def fetch_comments(username: str, password: str, shortcode: str) -> List[Tuple[str, str]]:
    L = instaloader.Instaloader()
    try:
        L.login(username, password)
    except Exception as e:
        raise RuntimeError(f"Instagram login failed: {e}")
    
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        comments = [(comment.owner.username, comment.text) for comment in post.get_comments()]
        return comments
    except Exception as e:
        raise RuntimeError(f"Failed to fetch comments: {e}")


# Helper: Generate a reply using GPT-4
def generate_reply(comment: str) -> str:
    prompt = (
        "You are an Instagram account owner. Reply to the following comment in a polite, helpful, and friendly way. "
        "Keep your reply concise and relevant.\n\n"
        f"Comment: {comment}\n\nReply:"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
        return reply
    except Exception as e:
        return f"[Error generating reply: {e}]"


if submit:
    if not username or not password or not shortcode:
        st.error("Please fill in all fields in the sidebar.")
    else:
        with st.spinner("Logging in and fetching comments..."):
            try:
                comments = fetch_comments(username, password, shortcode)
                if not comments:
                    st.info("No comments found for this post.")
                else:
                    st.success(f"Fetched {len(comments)} comments. Generating replies...")
            except Exception as e:
                st.error(str(e))
                comments = []

        if comments:
            results = []
            progress = st.progress(0)
            for i, (user, comment) in enumerate(comments):
                reply = generate_reply(comment)
                results.append({
                    "Commenter": user,
                    "Comment": comment,
                    "AI Reply": reply
                })
                progress.progress((i + 1) / len(comments))
                time.sleep(0.5)  # To avoid rate limits
            st.success("All replies generated!")
            st.dataframe(results, use_container_width=True)


st.markdown("---")
st.markdown("""
**Instructions:**
- Enter your Instagram credentials and the post shortcode in the sidebar.
- Your credentials are only used to log in via [instaloader](https://instaloader.github.io/) and are not stored.
- The OpenAI API key is read from `st.secrets['openai_api_key']` or defaults to `YOUR_OPENAI_API_KEY`.
- Replies are generated using GPT-4 and shown in a table below.
""") 