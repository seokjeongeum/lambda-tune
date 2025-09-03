import time
import json

import pandas as pd
import streamlit as st

from lambdatune.utils import get_dbms_driver
from lambdatune.dbgpt.ui.test import prompt, prompt_single_plan
from lambdatune.dbgpt.ui.common import QueryMetadataHandler


handler = QueryMetadataHandler()

st.markdown("# Regression Debugger")
st.markdown("### Analyze and improve query regressions using Large Language Models (LLMs). ")

with st.sidebar:
    st.title('DBG-PT')
    st.write('LLM-Assisted Query Regression Debugger')

    st.subheader('Database Systems')
    selected_dbms = st.sidebar.selectbox('Choose a Database System', ['Postgres'], key='selected_dbms')

st.markdown(
        """
        <style>
            .reportview-container .main .block-container{
                max-width: 90%;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### Fast Plan")
    st.markdown(f"#### Provide the fast query plan")
    plan_1 = st.text_area(label="plan1")

with col2:
    st.markdown("### Slow Plan")
    st.markdown(f"#### Provide the slow query plan")
    # st.write(last_plan.settings.split("\n"))
    plan_2 = st.text_area(label="plan2")


analyze_button = st.button("Analyze")

if analyze_button:
    st.markdown("### Explanation")

    with st.status("Sending plans to the LLM") as status:
        try:
            data = prompt(plan_1, plan_2, selected_dbms, fake_it=False, temperature=0)

            status.update(
                label="Success!", state="complete", expanded=False
            )

            plan_diff = data['plan_diff']
            reasoning = data['reasoning']
            commands = data['commands']

        except Exception as e:
            status.update(label="Failed: {}".format(str(e)), state="error", expanded=False)
            plan_diff = None
            reasoning = None
            commands = list()

    system_commands = list()
    index_commands = list()

    for cmd in commands:
        if "CREATE INDEX" not in cmd.upper() and "statement_timeout" not in cmd:
            system_commands.append(cmd)
        else:
            index_commands.append(cmd)

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    st.markdown("""
            <style>
                /* Target the CSS of the column containers directly */
                .stBlock > div:first-child > div {
                    border-right: 2px solid #000; /* Add a right border to all columns except the last one */
                }
                /* You might need to adjust the selector specificity depending on Streamlit's current implementation */
            </style>
            """, unsafe_allow_html=True)

    with col1:
        # Underlined markdown
        st.markdown("#### <u>Plan Differences</u>", unsafe_allow_html=True)
        st.write(plan_diff)
    with col2:
        st.markdown("#### <u>Reasoning</u>", unsafe_allow_html=True)
        st.write(reasoning)
    with col3:
        st.markdown("#### <u>Recommended Configuration</u>", unsafe_allow_html=True)
        st.write(system_commands)
    with col4:
        st.markdown("#### <u>Recommended Indexes</u>", unsafe_allow_html=True)
        st.write(index_commands)

    st.session_state["analyzed"] = True
    st.session_state["system_commands"] = system_commands
    st.session_state["index_commands"] = index_commands

if st.session_state.get("analyzed"):
    indexes = st.session_state["index_commands"]

    commands = '\n'.join(st.session_state.get("system_commands"))
    query_text = st.session_state.get("query_text")
    query_id = st.session_state.get("query_id")

    # Check if there are recommended index commands; If so, create the corresponding button
    if indexes:
        create_indexes = st.button("Create Indexes", help="Create the suggested indexes")

        if create_indexes:
            print("Creating indexes")
            cursor = get_dbms_driver(selected_dbms.upper(), db=db).cursor

            with st.status("Creating indexes...") as status:
                for c in indexes:
                    try:
                        st.write("Executing index command: " + c)
                        cursor.execute(c)
                    except Exception as e:
                        st.error(e)

                status.update(
                    label="Indexes created successfully!", state="complete", expanded=False
                )
