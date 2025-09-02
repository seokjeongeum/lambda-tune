import json
import logging
import os
import time
from lambdatune.config_selection import Configuration


import streamlit as st

from lambdatune.prompt_generator.compress_query_plans import generate_conditions, get_prompt, get_configurations
from lambdatune.llm.gpt4 import get_config_recommendations_with_compression

from lambdatune.ui.common import TPCH, JOB

# App title
st.set_page_config(page_title="λ-Tune")

st.write("# Configuration Generator")

st.markdown(
        """
        ### Generate configurations for a given benchmark and database system.
        """
    )

st.markdown(
        """
        Choose a database system, benchmark and the number of tokens from the left.
        """
    )

with st.sidebar:
    st.title('λ-Tune Configuration Generator')

    # st.subheader('LLM Settings')
    # # GPT version
    # gpt_version = st.sidebar.selectbox('Choose a GPT Version', ['gpt-4', 'gpt-3.5-turbo', 'gpt-3.5-turbo-2'],
    #                                    key='gpt_version', help="Choose a GPT version to use for the workload compressor.")
    # # API Key
    # key = st.text_input("API Key", type="password")
    #
    # # Test button
    # test_button = st.button('Test API Key', help="Test the API Key")

    # if test_button:
    #     with st.spinner("Testing API Key..."):
    #         time.sleep(2)
    #         # Test the API Key
    #         st.success("Connection successful!")

    st.subheader('Database Systems')
    selected_dbms = st.sidebar.selectbox('Choose a Database System', ['Postgres', 'MySQL'], key='selected_dbms')

    st.subheader('Benchmark')

    selected_benchmark = st.sidebar.selectbox('Choose a Benchmark', [TPCH, JOB],
                                          key='selected_benchmark')

    db = "tpch" if selected_benchmark == TPCH else "job"

    # Num Tokens
    num_tokens = st.sidebar.number_input('Number of Tokens', min_value=100, step=50, key='num_tokens',
                                         help="The number of tokens to use for the workload compressor")

    # Button
    start_button = st.sidebar.button('Extract Conditions', help="Extract conditions using the workload compressor.")

    generate_prompt_button = st.sidebar.button('Generate Prompt', help="Generate a prompt for the conditions obtained.")

    get_configuration_button = st.sidebar.button('Get Configuration from the LLM',
                                                 help="Get the configuration from the LLM.")

    # save_button = st.sidebar.button('Save Configuration', help="Save the obtained configuration to the database.")

    print(st.session_state.get("get_configuration_button"))

if start_button:
    st.write("Generating configurations...")
    conditions = generate_conditions(benchmark=db, dbms=selected_dbms.upper(), num_tokens=num_tokens, db=db)

    print("Conditions: ", conditions)

    for condition in conditions:
        st.write({
            condition: conditions[condition]
        })
    st.stop()

if generate_prompt_button:
    conditions = generate_conditions(benchmark=db, dbms=selected_dbms.upper(), num_tokens=num_tokens, db=db)
    prompt = get_prompt(selected_dbms, join_conditions=conditions, temperature=0.35)
    st.write("## Prompt")
    st.write([prompt['prompt']])
    # st.write(f"Number of Tokens: {prompt['num_tokens']}")

if get_configuration_button:
    st.session_state["get_configuration_button"] = True

    print("button:", st.session_state.get("get_configuration_button"))

    conditions = generate_conditions(benchmark=db, dbms=selected_dbms.upper(), num_tokens=num_tokens, db=db)
    prompt = get_prompt(selected_dbms, join_conditions=conditions, temperature=0.35)

    with st.spinner("Getting configurations from the LLM..."):
        configurations = get_config_recommendations_with_compression(
            dst_system=selected_dbms,
            join_conditions=conditions, relations=[],
            temperature=0.35,
            retrieve_response=True,
            indexes=True)

    st.success("Configurations obtained successfully")

    st.write("## Configurations")

    conf = configurations["response"]

    print(conf["choices"][0]["message"]["content"])

    s = json.loads(conf["choices"][0]["message"]["content"])["commands"]

    config = Configuration(s)
    st.info("Hints")
    st.write(list(config.get_configs()))

    st.info("Indexes")
    st.write(list(config.get_indexes().values()))

    # st.write("### System Configurations")
    # system_configurations = [c for c in configurations if "INDEX" not in c]
    # st.write(system_configurations)
    #
    # st.write("### Index Configurations")
    # index_configurations = [c for c in configurations if "CREATE INDEX" in c]
    # st.write(index_configurations)

# if save_button:
#     if not st.session_state.get("get_configuration_button"):
#         st.error("Please get the configuration first.")
#     else:
#         st.success("Configuration saved successfully!")
#         st.session_state["get_configuration_button"] = False