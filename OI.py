import streamlit as st
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
import pandas as pd
import time


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Ownership Research Agent",
    page_icon="🚢",
    layout="wide"
)


# ============================================================
# SEARCH
# ============================================================

def search_web(query, max_results=5):

    results = []

    try:

        with DDGS() as ddgs:

            search_results = ddgs.text(
                query,
                max_results=max_results
            )

            for r in search_results:

                if r.get("href"):

                    results.append({
                        "title": r.get("title", ""),
                        "link": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })

    except Exception as e:

        st.warning(f"Search failed: {query}")

    return results


# ============================================================
# WEB SCRAPER
# ============================================================

def get_text(url):

    try:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/151.0 Safari/537.36"
            )
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove unnecessary elements

        for tag in soup([
            "script",
            "style",
            "noscript",
            "header",
            "footer",
            "nav"
        ]):

            tag.decompose()

        text = soup.get_text(
            " ",
            strip=True
        )

        return text[:15000]

    except Exception:

        return ""


# ============================================================
# EXTRACT COMMERCIAL OWNER
# ============================================================

def extract_co(text):

    text_lower = text.lower()

    keywords = [
        "sold to",
        "acquired by",
        "purchased by",
        "bought by",
        "sale to"
    ]

    for keyword in keywords:

        if keyword in text_lower:

            position = text_lower.find(keyword)

            snippet = text[
                position + len(keyword):
                position + len(keyword) + 150
            ]

            return snippet.strip()

    return None


# ============================================================
# EXTRACT BENEFICIAL OWNER
# ============================================================

def extract_bo(text):

    text_lower = text.lower()

    keywords = [
        "owned by",
        "subsidiary of",
        "part of",
        "parent company",
        "ultimate owner",
        "beneficial owner"
    ]

    for keyword in keywords:

        if keyword in text_lower:

            position = text_lower.find(keyword)

            snippet = text[
                position + len(keyword):
                position + len(keyword) + 150
            ]

            return snippet.strip()

    return None


# ============================================================
# METHOD 1
# SALE / ACQUISITION RESEARCH
# ============================================================

def method1(vessel, previous_name):

    queries = []

    if vessel:

        queries.extend([
            f'"{vessel}" sold',
            f'"{vessel}" acquired',
            f'"{vessel}" purchased',
            f'"{vessel}" sold to'
        ])

    if previous_name:

        queries.extend([
            f'"{previous_name}" sold',
            f'"{previous_name}" acquired'
        ])

    results = []

    for query in queries:

        search_results = search_web(
            query,
            max_results=3
        )

        for result in search_results:

            text = get_text(
                result["link"]
            )

            if not text:
                continue

            co = extract_co(text)

            if co:

                results.append({
                    "Method": "Method 1 - Sale News",
                    "Query": query,
                    "CO Evidence": co,
                    "Source": result["link"]
                })

        # Small delay to avoid aggressive requests

        time.sleep(0.2)

    return results


# ============================================================
# METHOD 3
# OWNERSHIP / PARENT COMPANY
# ============================================================

def method3(ro):

    if not ro:
        return []

    queries = [
        f'"{ro}" owned by',
        f'"{ro}" subsidiary',
        f'"{ro}" parent company'
    ]

    results = []

    for query in queries:

        search_results = search_web(
            query,
            max_results=3
        )

        for result in search_results:

            text = get_text(
                result["link"]
            )

            if not text:
                continue

            bo = extract_bo(text)

            if bo:

                results.append({
                    "Method": "Method 3 - Ownership",
                    "Query": query,
                    "BO Evidence": bo,
                    "Source": result["link"]
                })

        time.sleep(0.2)

    return results


# ============================================================
# DECISION
# ============================================================

def decide(field, results):

    values = []

    for result in results:

        if field in result:

            value = result[field]

            if value:

                values.append(
                    value.strip()
                )

    if not values:

        return "Unknown"

    return max(
        set(values),
        key=values.count
    )


# ============================================================
# UI
# ============================================================

st.title(
    "🚢 Ownership Research Agent"
)

st.caption(
    "AI-assisted vessel ownership research"
)


# ============================================================
# INPUT
# ============================================================

col1, col2 = st.columns(2)

with col1:

    imo = st.text_input(
        "IMO Number"
    )

    vessel = st.text_input(
        "Present Vessel Name"
    )

with col2:

    previous_name = st.text_input(
        "Previous Vessel Name"
    )

    ro = st.text_input(
        "Registered Owner (RO)"
    )


# ============================================================
# RUN
# ============================================================

if st.button(
    "🔍 Run Ownership Research",
    type="primary"
):

    if not vessel and not imo:

        st.error(
            "Please provide at least IMO Number or Vessel Name."
        )

        st.stop()


    # --------------------------------------------------------
    # Research status
    # --------------------------------------------------------

    progress = st.progress(0)

    status = st.empty()


    # ========================================================
    # METHOD 1
    # ========================================================

    status.info(
        "🔎 Running Method 1: Vessel Sale / Acquisition..."
    )

    m1 = method1(
        vessel,
        previous_name
    )

    progress.progress(40)


    # ========================================================
    # METHOD 3
    # ========================================================

    status.info(
        "🔎 Running Method 3: Ownership / Parent Company..."
    )

    m3 = method3(
        ro
    )

    progress.progress(80)


    # ========================================================
    # COMBINE
    # ========================================================

    all_results = (
        m1 +
        m3
    )


    # ========================================================
    # DECISIONS
    # ========================================================

    co = decide(
        "CO Evidence",
        m1
    )

    bo = decide(
        "BO Evidence",
        m3
    )


    progress.progress(100)

    status.success(
        "Research completed."
    )


    # ========================================================
    # OUTPUT
    # ========================================================

    st.subheader(
        "🔎 Preliminary Results"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "IMO",
            imo if imo else "Not provided"
        )


    with col2:

        st.metric(
            "Commercial Owner / CO",
            co
        )


    with col3:

        st.metric(
            "Beneficial Owner / BO",
            bo
        )


    # ========================================================
    # CONFIDENCE
    # ========================================================

    evidence_count = len(all_results)


    if evidence_count >= 5:

        confidence = "Medium"

    elif evidence_count >= 2:

        confidence = "Low"

    else:

        confidence = "Very Low"


    st.write(
        f"**Research Confidence:** {confidence}"
    )


    # ========================================================
    # EVIDENCE
    # ========================================================

    st.subheader(
        "📄 Evidence & Sources"
    )


    if all_results:

        df = pd.DataFrame(
            all_results
        )

        st.dataframe(
            df,
            use_container_width=True
        )

    else:

        st.warning(
            "No usable evidence was found."
        )


    # ========================================================
    # RESEARCH DISCLAIMER
    # ========================================================

    st.info(
        "⚠️ These results are preliminary research findings. "
        "Ownership, management and commercial relationships "
        "should be independently verified before production use."
    )
