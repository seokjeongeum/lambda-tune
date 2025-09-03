import logging
import os

import streamlit as st

logging.basicConfig(level=logging.DEBUG)


def run():
    st.set_page_config(
        page_title="λ-Tune",
        page_icon="🧠"
    )

    st.sidebar.title("Test")

    st.write("# Welcome to λ-Tune!")

    st.sidebar.success("Select an option above.")

    st.markdown(
        """
        ### λ-Tune is a tool for automatic database tuning based on Large Language Models (LLMs).
        """
    )


if __name__ == "__main__":
    run()
