import openai
import json
import os
import re # Import the regular expression module

import tiktoken

from lambdatune.utils import get_llm, get_openai_key
import google.generativeai as genai
encoding = tiktoken.encoding_for_model(get_llm())
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = "https://api.perplexity.ai"


def get_response(text: str, temperature: float):
    try:
        # Ensure API key is configured (place configuration outside the function
        # or ensure it's run once before calling this function multiple times)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) # Uncomment if needed here
        
        system_instruction = "You are a helpful Database Administrator."
        gemini_model_name = "gemini-2.5-pro-exp-03-25" # Or your preferred model

        model = genai.GenerativeModel(
            model_name=gemini_model_name,
            system_instruction=system_instruction
        )

        messages = [{'role': 'user', 'parts': [text]}]

        generation_config = genai.types.GenerationConfig(
            temperature=temperature
        )

        response = model.generate_content(
            messages,
            generation_config=generation_config
        )
        return {
            "choices": [
                {
                    "message": {
                        "content": response.text,
                    }
                }
            ]
        }
    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return f"Error: {e}"
    response = openai.ChatCompletion.create(
        model="sonar",
        messages=[
            {"role": "system", "content": "You are a helpful Database Administrator."},
            {"role": "user", "content": text}
        ],
        temperature=temperature,
        web_search_options={"search_context_size": "low"},
    )

    return response


def output_format():
    format = """{\n\tcommands: [list of the SQL commands]\n}"""
    return (f"Your response should strictly consist of a python-compatible JSON response of the following schema. "
            f"Do not include any additional text in the prompt, such as descriptions or intros. Return just a"
            f"python-compatible list only. "
            "**Do NOT wrap individual commands in their own JSON objects (like {{\"command\": \"...\"}}).** Just include the command strings directly in the list. "
            f"\n{format}")


def get_config_recommendations_with_compression(dst_system,
                           relations,
                           temperature: float,
                           retrieve_response: bool = False,
                           join_conditions: dict = dict(),
                           system_specs=None,
                           indexes: bool = False,
                           indexes_only: bool = False,
                           hints=None,
                           filters:list=None,
                           workload_statistics:dict=None,
                           internal_metrics:dict=None,
                           query_plan:bool=False,
                           plans:list=list(),
                           ):
    """
    Generate a prompt for the user to provide configuration recommendations for a system. The prompt includes
    @param dst_system: The system for which the recommendations are requested
    @param relations: The relations and their occurrences in the workload
    @param join_conditions: The join conditions and their occurrences in the workload
    @param system_specs: The system specs
    @return: The prompt and the response
    """
    if not indexes_only:
        prompt = (f"Recommend some configuration parameters for {dst_system} to optimize the system's performance. "
                  f"Such parameters might include system-level configurations, like memory, query optimizer "
                  f"hints (such as join strategies, scan costs, parallelism, etc), "
                  f"or query-level configurations.")

        if True:
            prompt += "Include index recommendations (CREATE INDEX)."
        else:
            prompt += "Do not include index recommendations."
    else:
        prompt = "Give me index recommendations for the following input workload. The index names should be unique.\n"

    if workload_statistics:
        prompt += f"\nThe workload statistics are the following:\n"
        for stat in workload_statistics:
            prompt += f"{stat}: {workload_statistics[stat]}\n"

    if relations:
        prompt += f"\nThe relations and their occurrences in the workload are the following:\n"
        for rel in relations:
            prompt += f"{rel}, {relations[rel]}\n"

    if query_plan:
        prompt += f"\n\nThe query plan is the following:\n"
        for plan in plans:
            prompt += f"{(json.dumps(plans[0][1].root.info,indent=2))}\n"
    elif join_conditions:
        prompt += (f"\n\nEach row in the following list has the following format:\n"
                   f"{{a join key A}}:{{all the joins with A in the workload}}.\n\n")
        before=(len(prompt))
        for cond in join_conditions:
            prompt += f"{cond}: {join_conditions[cond]}\n"

    if filters:
        prompt += (f"\n\nEach row in the following list has the following format:\n"
                   f"{{a relation A}}:{{all the filters with A in the workload}}.\n\n")

        for cond in filters:
            prompt += f"{cond}\n"

    if internal_metrics:
        prompt += f"\nThe internal metrics are the following:\n"
        for metric in internal_metrics:
            prompt += f"{metric}: {internal_metrics[metric]}\n"

    if system_specs:
        prompt += f"\nThe workload runs on a system with the following specs:"

        for spec in system_specs.items():
            prompt += f"{spec[0]}: {spec[1]}\n"

    if hints:
        prompt += f"Hints: {hints}"

    prompt += "\n" + output_format()

    # print(len(encoding.encode(prompt)))

    print(prompt)

    resp = None

    if retrieve_response:
        resp_raw = get_response(prompt, temperature=temperature)

        # Check if the response is an error string
        if isinstance(resp_raw, str) and resp_raw.startswith("Error:"):
             print(f"LLM call failed: {resp_raw}")
             resp = resp_raw # Keep the error message
        elif isinstance(resp_raw, dict) and "choices" in resp_raw and resp_raw["choices"]:
            resp = resp_raw # Start with the raw response structure
            try:
                message_content_str = resp["choices"][0]["message"]["content"]

                # Attempt to parse the JSON content from the LLM
                parsed_content = json.loads(message_content_str)

                # Check if the parsed content has the expected structure
                if isinstance(parsed_content, dict) and "commands" in parsed_content:
                    original_commands = parsed_content.get("commands", [])
                    modified_commands = []

                    # Process only if commands is a list
                    if isinstance(original_commands, list):
                        for cmd in original_commands:
                            if isinstance(cmd, str) and cmd.strip().upper().startswith("CREATE INDEX"):
                                # Use re.sub for case-insensitive replacement of " IF NOT EXISTS "
                                # Pattern: space, "IF", space, "NOT", space, "EXISTS", space
                                # Replace with just a single space to maintain formatting
                                modified_cmd = re.sub(r'\s+IF\s+NOT\s+EXISTS\s+', ' ', cmd, flags=re.IGNORECASE)
                                modified_commands.append(modified_cmd.strip()) # .strip() removes potential leading/trailing whitespace
                            elif isinstance(cmd, str):
                                modified_commands.append(cmd) # Keep other string commands
                            # Else: If cmd is not a string, skip or handle as needed. Here we skip.
                    else:
                         # If 'commands' key exists but isn't a list, something is wrong with LLM output
                         print(f"Warning: Expected 'commands' to be a list, but got {type(original_commands)}. Keeping original content.")
                         # Keep resp as it was from get_response in this case

                    # Only update if modification was potentially successful (commands was a list)
                    if isinstance(original_commands, list):
                         # Rebuild the JSON content string with modified commands
                         modified_content_dict = {"commands": modified_commands}
                         # Use separators=(',', ':') for compact JSON string value if needed, but indent=2 is fine for readability
                         modified_content_string = json.dumps(modified_content_dict, indent=2)

                         # Update the response dictionary content
                         resp["choices"][0]["message"]["content"] = modified_content_string
                         print("\n--- MODIFIED LLM CONTENT ---")
                         print(modified_content_string)
                         print("----------------------------")

                else:
                    # Parsed content wasn't the expected {"commands": [...] } dict
                    print("Warning: LLM response JSON did not contain the expected 'commands' key at the top level. Cannot remove 'IF NOT EXISTS'.")
                    # Keep original resp

            except json.JSONDecodeError:
                print("Warning: LLM response content was not valid JSON. Cannot remove 'IF NOT EXISTS'. Raw content:")
                print(message_content_str)
                # Keep original resp (which contains the non-JSON string)
            except Exception as e:
                print(f"Warning: Error processing LLM response content for modification: {e}")
                # Keep original resp
        else:
            # get_response returned something unexpected (not error string, not valid dict)
            print(f"Warning: Unexpected return value from get_response: {resp_raw}")
            resp = str(resp_raw) # Convert to string as a fallback
        # resp = json.loads(str(resp))

    # num_tokens = len(encoding.encode(prompt))

    return {
        "prompt": prompt,
        "response": resp
    }

def get_config_recommendations_with_full_queries(dst_system, queries, temperature, retrieve_response: bool = False,
                                      system_specs=None):

    prompt = (f"Recommend some configuration parameters for {dst_system} to optimize the system's performance. "
              f"Such parameters might include system-level configurations, like memory, query optimizer or query-level "
              f"configuration.")

    if True:
        prompt += "Include index recommendations (CREATE INDEX)."
    else:
        prompt += "Do not include index recommendations."

    if queries:
        prompt += f"\nThe queries are the following\n"
        for query in queries:
            prompt += f"{query}\n"

    if system_specs:
        prompt += f"\nThe workload runs on a system with the following specs:"

        for spec in system_specs.items():
            prompt += f"{spec[0]}: {spec[1]}\n"

    prompt += output_format()

    # print(prompt)
    num_tokens = len(encoding.encode(prompt))
    print(num_tokens)

    resp = None

    if retrieve_response:
        resp = get_response(prompt, temperature=temperature)
        resp = json.loads(str(resp))

    # num_tokens = len(encoding.encode(prompt))

    return {
        "prompt": prompt,
        "response": resp
    }


def get_config_recommendations_with_ranked_conditions(dst_system,
                                      retrieve_response: bool = False,
                                      join_conditions=list(),
                                      system_specs=None):

    prompt = (f"Recommend some configuration parameters for {dst_system} to optimize the system's performance. "
              f"Include parameters of the following categories: 1. system-level configurations 2. memory "
              f"3. query optimization and 4. index recommendations (CREATE INDEX). "
              f"Provide a response that consists only from a comma-separated list of individual SQL commands. "
              f"Split the response into multiple lines if needed. ")

    prompt += f"\nThe join conditions are the following:\n"
    for cond in join_conditions:
        prompt += f"{cond}\n"

    if system_specs:
        prompt += f"\nThe workload runs on a system with the following specs:"

        for spec in system_specs.items():
            prompt += f"{spec[0]}: {spec[1]}\n"

    prompt += output_format()

    num_tokens = len(encoding.encode(prompt))

    response = None

    if retrieve_response:
        response = get_response(prompt)
        response = [d.replace("\"", "").replace(",", "") for d in response.split("\n")]

    return {
        "prompt": prompt,
        "response": response,
        "num_tokens": num_tokens,
    }


def get_configs(prompt: str):
    response = get_response(prompt)
    resp = [d.replace("\"", "").replace(",", "") for d in response.split("\n")]

    return resp


def fix_query_plan(old_plan, new_plan, config, system, system_specs):
    prompt = f"""
    Given the following query plan from {system}

    {old_plan}

    The system specs are the following. {system_specs}
    
    The following configuration was set 
    
    {config}
    
    the plan changed as follows:
    
    {new_plan}
    
    The new plan causes a query regression.
    
    Provide list of configurations to fix this regression.
    
    Classify the configurations to the following categories: memory, query planning decisions, indexes.

    The output should be python-compatible JSON.The structure per recommended configuration should be the following:

    {{
        "explanation": briefly explain why the plan changed and the regression causes,
        "configurations": {{
            "category_name": [
                {{
                    "configuration name": "the name"
                    "configuration value": "the exact value only"
                    "needs_restart": "True if the systems needs to restart, False otherwise",
                    "sql command": The SQL command to set that configuration
                }}
            ]
        }}
    }}
    
    Even if the plans are identical, provide some configuration to further improve the performance.

    The output should be strictly only the python compatible JSON response. Do not include any additional text and explanations.
    """

    print(prompt)

    return get_response(prompt)