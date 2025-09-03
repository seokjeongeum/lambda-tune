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

    # Executed queries
    st.markdown("### Executed Queries")
    executed_queries = handler.get_all_executed_queries()

    query_ids = executed_queries.keys()

    # Dropdown
    selected_query = st.sidebar.selectbox('Choose a Query', query_ids, key='selected_query',
                                          format_func=lambda x: f"{executed_queries[x][0].query_name} ({executed_queries[x][0].tag})")

failed = False
if selected_query:
    # Check last execution instance
    last_execution = executed_queries[selected_query][-1]

    failed = False
    if last_execution.failed:
        failed = True

    exec_times = [e.exec_time for e in executed_queries[selected_query]]
    ts = [e.ts for e in executed_queries[selected_query]]

    # Create a dataframe with execution times and timestamps
    df = pd.DataFrame({
        "Execution Time": exec_times,
        "Timestamp": ts,
        "Query Name": executed_queries[selected_query][0].query_name,
    })

    # fig = px.line(df, x="Timestamp", y="Execution Time", markers=True)
    # st.write(fig)
    st.line_chart(df, x="Timestamp", y="Execution Time")

    # Keep the fastest and the slowest query plans
    fastest = min(executed_queries[selected_query], key=lambda x: x.exec_time)
    last_plan = executed_queries[selected_query][-1]

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

if not failed:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Fastest Plan")
        st.markdown("Execution Time: {:.2f} seconds<br>Timestamp: {}".format(fastest.exec_time, fastest.ts), unsafe_allow_html=True)
        st.markdown(f"#### Plan")
        # st.write(fastest.settings.split("\n"))
        plan_1 = st.code(fastest.plan, language="sql", line_numbers=True)

    with col2:
        st.markdown("### Latest Plan")
        st.markdown("Execution Time: {:.2f} seconds<br>Timestamp: {}".format(last_plan.exec_time, last_plan.ts), unsafe_allow_html=True)
        st.markdown(f"#### Plan")
        # st.write(last_plan.settings.split("\n"))
        plan_2 = st.code(last_plan.plan, language="sql", line_numbers=True)
else:
    st.markdown("### The following query plan has failed due to the timeout.")
    plan = st.code(fastest.plan, language="sql", line_numbers=True)

analyze_button = st.button("Analyze")

if analyze_button:
    st.markdown("### Explanation")

    with st.status("Sending plans to the LLM") as status:
        try:
            if failed:
                data = prompt_single_plan(fastest.plan, selected_dbms, temperature=0)
            else:
                data = prompt(fastest.plan, last_plan.plan, selected_dbms, fake_it=False, temperature=0)

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
    st.session_state["query_text"] = executed_queries[selected_query][0].query_text
    st.session_state["query_id"] = selected_query

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
            db = executed_queries[selected_query][0].tag.lower()
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

    try_out = st.button("Try Out", help="Try out the suggested configuration")

    if try_out:
        st.markdown("### Execution")

        print(query_text)

        db = executed_queries[selected_query][0].tag.lower()
        driver = get_dbms_driver(selected_dbms.upper(), db=db)
        cursor = driver.cursor

        cursor.execute(f"{commands}\nEXPLAIN {query_text}")
        rows = cursor.fetchall()
        plan = "\n".join([row[0] for row in rows])

        with st.status("Trying out recommended configuration") as status:
            try:
                start = time.time()
                cursor.execute(f"SET statement_timeout = {10 * 1000}")
                cursor.execute(f"{commands}\n{query_text}")
                rows = cursor.fetchall()
                duration = time.time() - start

                handler.insert_executed_query(query_id, plan, duration, commands)

                st.markdown("### Results")
                st.markdown("Execution Time: {:.2f} seconds".format(duration))
                st.code(plan, language="sql", line_numbers=True)
                status.update(label="Success", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Failed due to timeout", state="error", expanded=False)
                handler.insert_executed_query(query_id, plan, 10, commands, meta=json.dumps({"timeout_fail": True, "timeout": 10}))
