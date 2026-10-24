import json
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Onchain Dashboards Portfolio",
    page_icon="📊",
    layout="wide",
)

BASE = Path(__file__).parent


@st.cache_data
def load_data():
    with open(BASE / "dashboards.json", encoding="utf-8") as f:
        return json.load(f)


data = load_data()
profile = data["profile"]
dashboards = data["dashboards"]

# ---------- Styles ----------
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; max-width: 1250px;}
    .hero {
        padding: 2.2rem 2rem; border-radius: 20px;
        background: linear-gradient(135deg, #1B1446 0%, #0F2A4A 55%, #0B0F1A 100%);
        border: 1px solid rgba(124,92,255,.35); margin-bottom: 1.2rem;
    }
    .hero h1 {margin: 0; font-size: 2.4rem;}
    .hero .tag {color: #A9B4FF; font-size: 1.15rem; margin-top: .3rem;}
    .hero .bio {color: #C9D0E8; margin-top: .8rem;}
    .social a {
        display: inline-block; margin: .8rem .5rem 0 0; padding: .35rem .9rem;
        border-radius: 999px; border: 1px solid rgba(255,255,255,.25);
        color: #fff !important; text-decoration: none; font-size: .9rem;
    }
    .social a:hover {background: rgba(124,92,255,.35);}
    .chip {
        display: inline-block; padding: .15rem .6rem; margin: 0 .3rem .3rem 0;
        border-radius: 999px; font-size: .75rem;
    }
    .chip.chain {background: rgba(124,92,255,.22); color: #C7B9FF;}
    .chip.topic {background: rgba(0,200,150,.18); color: #8CF2D2;}
    .chip.new {background: rgba(255,170,0,.2); color: #FFD27A;}
    .card-title {font-size: 1.15rem; font-weight: 700; margin: .4rem 0 .2rem;}
    .card-desc {color: #AEB6CF; font-size: .9rem; min-height: 2.6rem;}
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px; transition: transform .15s, box-shadow .15s;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-3px); box-shadow: 0 8px 24px rgba(124,92,255,.25);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Hero ----------
links_html = "".join(
    f'<a href="{url}" target="_blank">{name}</a>'
    for name, url in profile.get("links", {}).items()
    if url
)
st.markdown(
    f"""
    <div class="hero">
      <h1>{profile['name']}</h1>
      <div class="tag">{profile['tagline']}</div>
      <div class="bio">{profile.get('bio', '')}</div>
      <div class="social">{links_html}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- KPIs ----------
all_chains = sorted({c for d in dashboards for c in d.get("chains", [])})
all_topics = sorted({t for d in dashboards for t in d.get("topics", [])})

k1, k2, k3 = st.columns(3)
k1.metric("Dashboards", len(dashboards))
k2.metric("Chains covered", len(all_chains))
k3.metric("Topics", len(all_topics))

st.divider()

# ---------- Filters ----------
f1, f2, f3 = st.columns([2, 2, 3])
sel_chains = f1.multiselect("Chain", all_chains)
sel_topics = f2.multiselect("Topic", all_topics)
query = f3.text_input("Search", placeholder="Search by name or description...")


def matches(d):
    if sel_chains and not set(sel_chains) & set(d.get("chains", [])):
        return False
    if sel_topics and not set(sel_topics) & set(d.get("topics", [])):
        return False
    if query:
        q = query.lower()
        if q not in d["title"].lower() and q not in d.get("description", "").lower():
            return False
    return True


def is_new(d, days=30):
    try:
        return datetime.now() - datetime.fromisoformat(d["date"]) < timedelta(days=days)
    except Exception:
        return False


def render_card(d):
    with st.container(border=True):
        img = d.get("image")
        if img and (BASE / img).exists():
            st.image(str(BASE / img), use_container_width=True)
        chips = "".join(f'<span class="chip chain">{c}</span>' for c in d.get("chains", []))
        chips += "".join(f'<span class="chip topic">{t}</span>' for t in d.get("topics", []))
        if is_new(d):
            chips += '<span class="chip new">New</span>'
        st.markdown(
            f"""
            <div>{chips}</div>
            <div class="card-title">{d['title']}</div>
            <div class="card-desc">{d.get('description', '')}</div>
            """,
            unsafe_allow_html=True,
        )
        b1, b2 = st.columns(2)
        b1.link_button("Open Dashboard", d["url"], use_container_width=True, type="primary")
        if d.get("github"):
            b2.link_button("GitHub", d["github"], use_container_width=True)


def render_grid(items, cols=3):
    for i in range(0, len(items), cols):
        row = st.columns(cols)
        for col, d in zip(row, items[i : i + cols]):
            with col:
                render_card(d)


# ---------- Featured ----------
filtering = bool(sel_chains or sel_topics or query)
featured = [d for d in dashboards if d.get("featured")]
if featured and not filtering:
    st.subheader("⭐ Featured")
    render_grid(featured, cols=min(3, len(featured)))
    st.divider()

# ---------- All dashboards ----------
st.subheader("All Dashboards")
items = sorted(
    [d for d in dashboards if matches(d)],
    key=lambda d: d.get("date", ""),
    reverse=True,
)
if items:
    render_grid(items, cols=3)
else:
    st.info("No dashboards match your filters.")

# ---------- Footer ----------
st.divider()
x_link = profile.get("links", {}).get("X", "")
st.caption(f"Want a custom dashboard? DM me on [X]({x_link}).")
