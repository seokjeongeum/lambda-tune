import os
import time

import streamlit as st

import json
from lambdatune.utils import get_dbms_driver
from lambdatune.dbgpt.ui.common import QueryMetadataHandler

st.markdown("# Interactive Query Executor")
st.markdown("### Analyze query performance over different tuning knobs.")

handler = QueryMetadataHandler()

with st.sidebar:
    st.title('DBG-PT - Query Explorer')

    st.subheader('Settings')
    selected_dbms = st.sidebar.selectbox('Choose a Database System', ['Postgres'], key='selected_dbms')

    # Chose a Query Tag
    tags = sorted(handler.get_all_tags())
    selected_tag = st.sidebar.selectbox('Choose a Query Tag', tags, key='selected_tag')

    driver = get_dbms_driver(selected_dbms.upper(), db=selected_tag.lower())
    cursor = driver.cursor

    # Chose a Query
    queries = [(d[1], d) for d in handler.get_queries_by_tag(selected_tag)]
    queries = dict(queries)
    selected_query = st.sidebar.selectbox('Choose a Query', queries.keys(), key='selected_query')

    timeout = st.number_input("Timeout (seconds)", value=10, min_value=1, key='timeout')

    explain_col, execute_col = st.columns([1, 1])

    explain_button = st.button("Explain")
    execute_button = st.button("Execute")

    st.markdown("### Settings")
    settings = st.text_area("Settings", label_visibility="hidden")

query_column, explain_col = st.columns([1, 1])

if selected_query:
    with query_column:
        st.markdown("### Query")
        query_text = queries[selected_query][2]
        query_id = queries[selected_query][0]
        st.code(query_text, language="sql", line_numbers=True)


if execute_button or explain_button:
    with explain_col:
        st.markdown("### Query Plan")
        cursor.execute(f"{settings}\nEXPLAIN {query_text}")
        rows = cursor.fetchall()

        plan = "\n".join([row[0] for row in rows])

        st.code(plan, language="sql", line_numbers=True)

    if execute_button:
        start = time.time()
        timeout_fail = False

        with st.status("Executing query") as status:
            try:
                cursor.execute(f"SET statement_timeout = {timeout * 1000}")
                cursor.execute(f"{settings}\n{query_text}")
                rows = cursor.fetchall()
                status.update(label="Success", state="complete", expanded=False)
            except Exception as e:
                st.error(str(e))
                rows = str(e)
                timeout_fail = True
                status.update(label="Failed due to timeout", state="error", expanded=False)

        duration = time.time() - start

        st.markdown("### Results")
        st.write(rows)

        st.markdown("#### Performance")
        st.code(f"Execution Time: {duration} seconds")

        handler.insert_executed_query(query_id, plan, duration, settings,
                                      json.dumps({"timeout_fail": timeout_fail, "timeout": timeout}))
