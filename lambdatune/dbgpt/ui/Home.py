import logging

import streamlit as st

import os

from lambdatune.utils import get_dbms_driver

logging.basicConfig(level=logging.DEBUG)


def run():
    st.set_page_config(
        page_title="DBG-PT",
        page_icon="🧠",
        layout="wide"
    )

    st.sidebar.title("Test")

    st.write("# Welcome to DBG-PT!")

    st.sidebar.success("Select an option above.")

    st.markdown(
        """
        ### DBG-PT is a Query Regression Debugging Tool, powered by Large Language Models (LLMs).
        """
    )

    reset_demo = st.button("Reset Demo")
    reset_indexes = st.button("Reset Indexes")

    if reset_demo:
        os.remove("lambda_pi.db")

    if reset_indexes:
        get_dbms_driver("POSTGRES", db="tpch").drop_all_non_pk_indexes()


if __name__ == "__main__":
    run()
