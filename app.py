import os
import re
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st

from analysis import ConversationAnalysis, DEFAULT_FRAMEWORK


def main():
    st.set_page_config(page_title="Edoofa Conversation Audit", layout="wide")

    st.title("Edoofa Counselor Conversation Audit")
    st.markdown(
        "Upload one or more WhatsApp-style conversation files and generate an audit report of communication quality, tone, consistency, and pressure signals."
    )

    with st.expander("Audit Framework"):
        for category in DEFAULT_FRAMEWORK:
            st.markdown(f"**{category['name']}**: {category['description']}")
            st.markdown(f"- Measures: {category['measures']}")
            st.markdown(f"- Why it matters: {category['why']}")

    uploaded_files = st.file_uploader(
        "Upload conversation files", type=["txt", "md", "csv"], accept_multiple_files=True
    )

    google_sheet_id = st.text_input("Optional Google Sheet ID", help="If provided, findings will be pushed to this Google Sheet when " "credentials are configured.")
    if st.button("Run Audit"):
        if not uploaded_files:
            st.warning("Please upload at least one conversation file.")
            return

        conversations = []
        for uploaded in uploaded_files:
            text = uploaded.read().decode("utf-8", errors="ignore")
            conversations.append({"name": uploaded.name, "content": text})

        analyzer = ConversationAnalysis(DEFAULT_FRAMEWORK)
        report = analyzer.analyze_conversations(conversations)

        st.success("Audit completed")
        st.subheader("Summary Findings")
        st.write(report["summary"])

        for finding in report["findings"]:
            st.markdown(f"### {finding['title']}")
            st.write(f"**Severity:** {finding['severity']}")
            st.write(f"**Category:** {finding['category']}")
            st.write(f"**Description:** {finding['description']}")
            st.write(f"**Evidence:**")
            for evidence in finding["evidence"]:
                st.write(f"- {evidence}")
            st.write("---")

        if google_sheet_id:
            try:
                sheet_url = analyzer.push_to_google_sheet(report, google_sheet_id)
                st.info(f"Findings pushed to Google Sheet: {sheet_url}")
            except Exception as exc:
                st.error(f"Google Sheets update failed: {exc}")


if __name__ == "__main__":
    main()
