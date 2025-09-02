import pandas as pd
import streamlit as st
from langchain_core.messages import ToolMessage, AIMessage

from lambdatune.dbgpt.agents.debugger import DebuggingAgent
from lambdatune.utils import get_dbms_driver
from lambdatune.dbgpt.ui.common import QueryMetadataHandler


handler = QueryMetadataHandler()

st.markdown("# Agentic Regression Debugger")
st.markdown("### Analyze and improve query regressions using LLM Agents ")

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


    debug_button = st.button("Debug")

    if debug_button:
        # Keep the fastest and the slowest query plans
        fastest = min(executed_queries[selected_query], key=lambda x: x.exec_time)
        last_plan = executed_queries[selected_query][-1]

        query_text = executed_queries[selected_query][0].query_text

        db = executed_queries[selected_query][0].tag.lower()
        cursor = get_dbms_driver(selected_dbms.upper(), db=db).cursor

        agent = DebuggingAgent(
            query=query_text,
            cursor=cursor,
            fast_plan=fastest.plan,
            slow_plan=last_plan.plan,
        )

        with st.status("Sending plans to the LLM"):
            results = agent.debug()

            idx = 1

            while idx < len(results):
                print(idx, type(results[idx]))

                if isinstance(results[idx], AIMessage):
                    settings = results[idx].tool_calls
                    num_settings = len(settings)

                    st.write(results[idx].content)

                    for setting_idx, setting in enumerate(settings):
                        st.write("Trying the following settings")
                        st.text(setting["args"]["settings"])
                        st.write("Result")
                        st.text(results[idx + setting_idx + 1].content)

                idx += 1