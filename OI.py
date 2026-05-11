import streamlit as st
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import pandas as pd

# ---------------- SEARCH ---------------- #
def search_web(query):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=5):
            results.append({"title": r["title"], "link": r["href"]})
    return results

# ---------------- SCRAPER ---------------- #
def get_text(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.get_text(" ", strip=True)
    except:
        return ""

# ---------------- EXTRACTORS ---------------- #
def extract_co(text):
    keywords = ["sold to", "acquired by", "purchased by", "bought by"]
    for kw in keywords:
        if kw in text.lower():
            snippet = text.lower().split(kw)[1][:80]
            return snippet.strip()
    return None

def extract_bo(text):
    keywords = ["owned by", "subsidiary of", "part of"]
    for kw in keywords:
        if kw in text.lower():
            snippet = text.lower().split(kw)[1][:80]
            return snippet.strip()
    return None

# ---------------- METHOD 1 ---------------- #
def method1(vessel, prev):
    queries = [
        f"{prev} sold",
        f"{vessel} acquired",
        f"{vessel} purchased vessel",
        f"{vessel} sold to"
    ]
    results = []

    for q in queries:
        search_results = search_web(q)
        for r in search_results:
            text = get_text(r["link"])
            co = extract_co(text)
            if co:
                results.append({
                    "Method": "Method 1 (Sale News)",
                    "Query": q,
                    "CO": co,
                    "Source": r["link"]
                })
    return results

# ---------------- METHOD 3 ---------------- #
def method3(ro):
    queries = [
        f"{ro} owned by",
        f"{ro} subsidiary",
        f"{ro} annual report"
    ]
    results = []

    for q in queries:
        search_results = search_web(q)
        for r in search_results:
            text = get_text(r["link"])
            bo = extract_bo(text)
            if bo:
                results.append({
                    "Method": "Method 3 (Ownership)",
                    "Query": q,
                    "BO": bo,
                    "Source": r["link"]
                })
    return results

# ---------------- DECISION ---------------- #
def decide(field, results):
    values = [r[field] for r in results if field in r and r[field]]
    if not values:
        return "Unknown"
    return max(set(values), key=values.count)

# ---------------- UI ---------------- #
st.title("🚢 Ownership Research Agent (Demo)")

vessel = st.text_input("Vessel Name")
prev = st.text_input("Previous Name")
ro = st.text_input("Registered Owner (RO)")

if st.button("Run Research"):

    st.info("Running Method 1: Sale News...")
    m1 = method1(vessel, prev)

    st.info("Running Method 3: Ownership Search...")
    m3 = method3(ro)

    all_results = m1 + m3

    # Decisions
    co = decide("CO", m1)
    bo = decide("BO", m3)

    # ---------------- OUTPUT ---------------- #
    st.subheader("🔎 Final Output")

    col1, col2 = st.columns(2)
    col1.metric("Commercial Operator (CO)", co)
    col2.metric("Beneficial Owner (BO)", bo)

    # Confidence (simple logic)
    confidence = "High" if len(all_results) > 3 else "Medium" if len(all_results) > 1 else "Low"
    st.write(f"**Confidence:** {confidence}")

    st.subheader("📄 Evidence & Methods Used")

    if all_results:
        df = pd.DataFrame(all_results)
        st.dataframe(df)
    else:
        st.warning("No strong evidence found. Tag as UNKNOWN.")
