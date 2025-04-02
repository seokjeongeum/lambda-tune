import openai
import json
import os
import re  # Import the regular expression module

import tiktoken

from lambdatune.plan_utils.postgres_plan_utils import PostgresPlan

# Assuming get_llm() exists and returns a valid model name for tiktoken
try:
    # Replace get_llm() with a specific model if it's not defined elsewhere
    # encoding = tiktoken.encoding_for_model(get_llm())
    encoding = tiktoken.encoding_for_model("gpt-4")  # Example: use a known model
except Exception as e:
    print(
        f"Warning: Could not get encoding for LLM. Using default cl100k_base. Error: {e}"
    )
    encoding = tiktoken.get_encoding("cl100k_base")


import google.generativeai as genai

# --- Configure API keys (ensure these are set in your environment) ---
# These lines configure OpenAI/Perplexity but are effectively bypassed by the get_response logic
# openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_base = "https://api.perplexity.ai"


# --- Modified get_response focusing on Gemini ---
def get_response(text: str, temperature: float):
    """
    Calls the Gemini API and returns a dictionary mimicking OpenAI's structure,
    or an error string.
    """
    try:
        # Configure API key if not already done globally
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Define system instruction and model
        system_instruction = "You are a helpful Database Administrator."
        gemini_model_name = "gemini-2.5-pro-exp-03-25"  # DO NOT CHANGE THIS LINE

        model = genai.GenerativeModel(
            model_name=gemini_model_name, system_instruction=system_instruction
        )

        messages = [{"role": "user", "parts": [text]}]

        # Set up generation config, requesting JSON output
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",  # Request JSON output
        )

        # Generate content
        response = model.generate_content(messages, generation_config=generation_config)

        # Check for valid text output
        if hasattr(response, "text") and response.text:
            # Return in OpenAI-like format
            return {
                "choices": [
                    {
                        "message": {
                            "content": response.text,  # This should be the JSON string
                        }
                    }
                ]
            }
        else:
            # Handle failure/blocking cases
            finish_reason = (
                response.candidates[0].finish_reason
                if response.candidates
                else "Unknown"
            )
            safety_feedback = (
                response.prompt_feedback if response.prompt_feedback else "None"
            )
            print(
                f"Warning: Gemini response did not contain text. Finish Reason: {finish_reason}, Safety Feedback: {safety_feedback}"
            )
            try:
                candidate_content = (
                    response.candidates[0].content.parts[0].text
                    if response.candidates
                    and response.candidates[0].content
                    and response.candidates[0].content.parts
                    else "No content found"
                )
                print(f"Candidate Content (if available): {candidate_content}")
            except Exception:
                pass
            return f"Error: Gemini generation failed or was blocked. Reason: {finish_reason}"

    except ValueError as ve:
        print(f"An error occurred during Gemini API call (ValueError): {ve}")
        try:
            prompt_feedback = getattr(ve, "prompt_feedback", None)
            if prompt_feedback:
                print(f"Prompt Feedback: {prompt_feedback}")
                return f"Error: Gemini call failed due to prompt content. Feedback: {prompt_feedback}"
        except Exception:
            pass
        return f"Error: {ve}"
    except Exception as e:
        print(f"An unexpected error occurred during Gemini API call: {e}")
        import traceback
        print(traceback.format_exc())
        return f"Error: {e}"

# --- Refined output_format ---
def output_format():
    format_schema = '{\n  "commands": ["SQL command 1", "SQL command 2", ...]\n}'
    return (
        f"Your response should strictly consist of a single, valid JSON object matching the following schema. "
        f"Do not include any text before or after the JSON object, including markdown fences (```json ... ```).\n\n"
        f"Schema:\n{format_schema}\n\n"
        f"Ensure each element in the 'commands' list is a string containing a complete SQL command. "
        f"Do not include any SQL comments (`--` or `/* */`) in the command strings. " # Added comment restriction
        f'Do **not** wrap individual commands in their own JSON objects (e.g., do not use {{"command": "..."}}).'
    )

# --- Helper to remove comments ---
def remove_sql_comments(sql_command: str) -> str:
    """Removes single-line and multi-line SQL comments."""
    # Remove multi-line comments /* ... */ (non-greedy)
    sql_no_block_comments = re.sub(r"/\*.*?\*/", "", sql_command, flags=re.DOTALL)
    # Remove single-line comments -- ...
    sql_no_comments = re.sub(r"--.*", "", sql_no_block_comments)
    return sql_no_comments.strip()


# --- Helper function to process index commands ---
def process_create_index_command(command: str) -> list[str]:
    """
    Processes a CREATE INDEX command according to the rules:
    - Removes 'IF NOT EXISTS'.
    - Removes 'CONCURRENTLY'.
    - Removes 'WHERE' clause (converts partial to full).
    - Removes 'USING <method>' clause (defaults to B-tree).
    - Splits multi-column index into multiple single-column indexes with derived names.
    - Returns a list of resulting command strings (usually 1, more for multi-column).
    """
    processed_commands = []
    original_command_for_log = command  # Keep original for logging
    command_upper = command.strip().upper()

    # Remove comments first before checking structure
    command = remove_sql_comments(command)
    command_upper = command.strip().upper() # Re-evaluate after removing comments

    if not command_upper.startswith("CREATE INDEX"):
        # Ensure non-index commands end with a semicolon if they don't already
        if command and not command.endswith(";"):
            command += ";"
        return [command] if command else [] # Return cleaned or empty list


    # --- Initial Cleaning Steps (Comments already removed) ---
    # 1. Remove IF NOT EXISTS (case-insensitive)
    command_no_ine = re.sub(
        r"\s+IF\s+NOT\s+EXISTS\s+", " ", command, flags=re.IGNORECASE
    ).strip()

    # 2. Remove CONCURRENTLY (case-insensitive)
    command_no_concurrently = re.sub(
        r"(INDEX)\s+CONCURRENTLY\s+", r"\1 ", command_no_ine, flags=re.IGNORECASE
    ).strip()
    command_no_concurrently = re.sub(
        r"CREATE\s+CONCURRENTLY\s+(INDEX)",
        r"CREATE \1",
        command_no_concurrently,
        flags=re.IGNORECASE,
    ).strip()

    # 3. Remove WHERE clause (convert partial to full, case-insensitive)
    parts = re.split(
        r"\s+WHERE\s+", command_no_concurrently, maxsplit=1, flags=re.IGNORECASE
    )
    command_no_where = parts[0].strip()

    # 4. Remove USING clause (convert to default B-tree)
    command_cleaned = re.sub(
        r"\s+USING\s+\S+\s*(?=\()", " ", command_no_where, flags=re.IGNORECASE
    ).strip()
    if command_cleaned != command_no_where:
        print(f"Removed USING clause from: {original_command_for_log}")

    # 5. Parse index name, table, and columns from the *now fully cleaned* command
    match = re.match(
        r"CREATE\s+INDEX\s+(?P<name>\S+)\s+ON\s+(?P<table>\S+)\s*\((?P<cols>.*?)\)\s*;?",
        command_cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        print(
            f"Warning: Could not parse final CREATE INDEX structure: {original_command_for_log}. Keeping command as is (after cleaning)."
        )
        if not command_cleaned.endswith(";"):
            command_cleaned += ";"
        return [command_cleaned] if command_cleaned else []

    # --- Process columns ---
    index_name = match.group("name")
    table_name = match.group("table")
    cols_str = match.group("cols").strip()

    columns = [c.strip() for c in re.split(r"\s*,\s*", cols_str) if c.strip()]

    if not columns:
        print(f"Warning: No columns found after parsing index: {original_command_for_log}. Discarding.")
        return []

    if len(columns) == 1:
        # Single-column index (fully cleaned)
        single_col_command = f"CREATE INDEX {index_name} ON {table_name} ({columns[0]})"
        if not single_col_command.endswith(";"):
            single_col_command += ";"
        processed_commands.append(single_col_command)
    else:
        # Multi-column index: Split
        print(f"Splitting multi-column index: {original_command_for_log}")
        for i, col in enumerate(columns):
            col_name_part = re.sub(r"[^a-zA-Z0-9_]+", "_", col).strip("_")
            if not col_name_part:
                col_name_part = f"col{i+1}"

            new_index_name = f"{index_name}_col{i+1}_{col_name_part}"
            new_index_name = new_index_name[:63]

            split_command = f"CREATE INDEX {new_index_name} ON {table_name} ({col})"
            if not split_command.endswith(";"):
                split_command += ";"
            processed_commands.append(split_command)
            print(f"  -> Generated: {split_command}")

    # Final check for empty strings in the result list just in case
    return [cmd for cmd in processed_commands if cmd]


# --- Modified get_config_recommendations_with_compression ---
def get_config_recommendations_with_compression(
    dst_system,
    relations,
    temperature: float,
    retrieve_response: bool = False,
    join_conditions: dict = dict(),
    system_specs=None,
    indexes: bool = True,  # Defaulting to True
    indexes_only: bool = False,
    hints=None,
    filters: list = None,
    workload_statistics: dict = None,
    internal_metrics: dict = None,
    query_plan: bool = False,
    plans: list = list(),
    data_definition_language:str=None,
):
    """
    Generate a prompt for recommendations, process the response to handle different
    JSON formats, transform indexes, and remove comments.
    """
    # ... (prompt building logic remains the same) ...
    if not indexes_only:
        prompt = (f"Recommend some configuration parameters for {dst_system} to optimize the system's performance. "
                  f"Such parameters might include system-level configurations, like memory, query optimizer "
                  f"hints (such as join strategies, scan costs, parallelism, etc), "
                  f"or query-level configurations.")
        if indexes:
            prompt += " Include index recommendations (CREATE INDEX)."
        else:
             prompt += " Do not include index recommendations."
    else:
        prompt = f"Give me index recommendations for the following input workload for {dst_system}. The index names should be unique.\n"
    if data_definition_language:        
        prompt += "The workload contains the following DDL statements:\n"
        prompt += f"{data_definition_language}\n"
    if workload_statistics:
        prompt += "\nThe workload statistics are the following:\n" + "\n".join(f"{stat}: {workload_statistics[stat]}" for stat in workload_statistics)
    if relations:
        prompt += "\nThe relations and their occurrences in the workload are the following:\n" + "\n".join(f"{rel}, {relations[rel]}" for rel in relations)
    elif workload_statistics and 'table_access_frequency' in workload_statistics:
         prompt += "\nThe table access frequency is:\n" + json.dumps(workload_statistics['table_access_frequency'], indent=2)
    if query_plan and plans:
        prompt += "\n\nThe query plan is the following:\n"
        for plan_item in plans:
            # Check if plan_item has at least two elements and the second is PostgresPlan
            if len(plan_item) > 1 and isinstance(plan_item[1], PostgresPlan):
                # Safely access root and info if they exist
                if hasattr(plan_item[1], "root") and hasattr(plan_item[1].root, "info"):
                    prompt += json.dumps(plan_item[1].root.info, indent=2) + "\n"
                else:
                    # Fallback if structure is slightly different but still PostgresPlan
                    try:
                        prompt += json.dumps(plan_item[1].to_dict(), indent=2) + "\n" # Assuming a to_dict() method
                    except Exception as plan_err:
                        print(f"Could not serialize plan object: {plan_err}")
                        prompt += str(plan_item[1]) + "\n" # Basic string fallback
            # Handle cases where the second element might be a plain dict
            elif len(plan_item) > 1 and isinstance(plan_item[1], dict):
                 prompt += json.dumps(plan_item[1], indent=2) + "\n"
            else: # Fallback for other unexpected structures
                prompt += str(plan_item) + "\n"
    elif join_conditions:
        prompt += "\n\nJoin conditions found in the workload:\n" + "\n".join(f"{cond}: {join_conditions[cond]}" for cond in join_conditions)
    if filters:
        prompt += "\n\nFilters found in the workload:\n" + "\n".join(f"{cond}" for cond in filters)
    if internal_metrics:
        prompt += "\nThe internal metrics are the following:\n" + "\n".join(f"{metric}: {internal_metrics[metric]}" for metric in internal_metrics)
    if system_specs:
        prompt += "\nThe workload runs on a system with the following specs:\n" + "\n".join(f"{spec}: {system_specs[spec]}" for spec in system_specs)
    if hints:
        prompt += f"\nHints: {hints}"
    prompt += "\n\n" + output_format()


    print("--- PROMPT ---")
    print(prompt)
    print("--------------")

    resp = None

    if retrieve_response:
        resp_raw = get_response(prompt, temperature=temperature)

        # Handle error string from get_response
        if isinstance(resp_raw, str) and resp_raw.startswith("Error:"):
            print(f"LLM call failed: {resp_raw}")
            resp = resp_raw
        # Handle successful dictionary response
        elif (
            isinstance(resp_raw, dict) and "choices" in resp_raw and resp_raw["choices"]
        ):
            resp = resp_raw  # Start with the raw structure
            processed_correctly = False  # Flag to track if processing succeeded
            message_content_str = "" # Initialize for broader scope in error handling
            try:
                message_content_str = resp["choices"][0]["message"]["content"]
                # Clean potential markdown fences before parsing
                message_content_str = re.sub(
                    r"^```json\s*", "", message_content_str, flags=re.MULTILINE
                )
                message_content_str = re.sub(
                    r"\s*```$", "", message_content_str, flags=re.MULTILINE
                ).strip() # Add strip here too

                parsed_content = json.loads(message_content_str)
                original_commands = None

                # --- Detect and Extract Commands based on received format ---
                if (
                    isinstance(parsed_content, dict)
                    and "commands" in parsed_content
                    and isinstance(parsed_content["commands"], list)
                ):
                    print("Detected format: {'commands': [...]}")
                    original_commands = parsed_content["commands"]
                elif isinstance(parsed_content, list):
                    if all(isinstance(item, str) for item in parsed_content):
                        print("Detected format: List of strings [...]")
                        original_commands = parsed_content
                    elif all(
                        isinstance(item, dict) and "command" in item
                        for item in parsed_content
                    ):
                        print("Detected format: List of dicts [{'command': ...}, ...]")
                        original_commands = [
                            item["command"]
                            for item in parsed_content
                            if isinstance(item.get("command"), str)
                        ]
                    else: # Try to handle dicts with 'recommendations' inside a list
                        if all(isinstance(item, dict) and 'recommendations' in item for item in parsed_content):
                             print("Detected format: List containing {'recommendations': [...]}")
                             original_commands = []
                             for outer_item in parsed_content:
                                 recs = outer_item.get('recommendations', [])
                                 if isinstance(recs, list):
                                     original_commands.extend([
                                         item["command"]
                                         for item in recs
                                         if isinstance(item, dict)
                                         and isinstance(item.get("command"), str)
                                     ])

                        else:
                            print("Warning: Detected list format, but content is mixed or invalid.")
                elif isinstance(parsed_content, dict) and 'recommendations' in parsed_content and isinstance(parsed_content['recommendations'], list):
                     # Handle the direct {'recommendations': [...]} case
                     print("Detected format: {'recommendations': [{'command':...}]}")
                     original_commands = [item["command"] for item in parsed_content['recommendations'] if isinstance(item, dict) and isinstance(item.get("command"), str)]
                else:
                    print("Warning: LLM response JSON is not in any expected format.")


                # --- Process extracted commands if found ---
                if original_commands is not None:
                    processed_commands_final = []
                    for cmd in original_commands:
                        if not isinstance(cmd, str):
                            print(
                                f"Warning: Skipping non-string item in commands list: {cmd}"
                            )
                            continue

                        # Process command (handles CREATE INDEX transformation and keeps others)
                        # remove_sql_comments is now called INSIDE process_create_index_command
                        resulting_cmds = process_create_index_command(cmd)
                        processed_commands_final.extend(resulting_cmds)

                    # Final filtering for empty strings that might result from comment-only lines
                    processed_commands_final = [c for c in processed_commands_final if c]

                    # Rebuild JSON content in the TARGET format
                    final_content_dict = {"commands": processed_commands_final}
                    final_content_string = json.dumps(final_content_dict, indent=2)

                    # Update the response dictionary content to the standard format
                    resp["choices"][0]["message"]["content"] = final_content_string
                    processed_correctly = True  # Mark as successfully processed
                    print("\n--- STANDARDIZED & PROCESSED LLM CONTENT (Comments Removed) ---")
                    print(final_content_string)
                    print("-------------------------------------------------------------")

                else: # No valid commands extracted
                    # Removed the specific 'recommendations' check here as it's handled above now.
                    print(
                        "Warning: Could not extract commands from the received JSON structure."
                    )

                if not processed_correctly:
                    # If processing failed or wasn't possible, keep the original parsed string
                    resp["choices"][0]["message"]["content"] = message_content_str
                    print("\n--- KEPT ORIGINAL (UNPROCESSABLE) LLM CONTENT ---")
                    print(message_content_str)
                    print("------------------------------------------------")

            except json.JSONDecodeError:
                print(
                    "Critical Warning: LLM response content was not valid JSON. Cannot process commands. Raw content:"
                )
                print(message_content_str)
                # Keep the original NON-JSON string in the response
                resp["choices"][0]["message"]["content"] = message_content_str

            except Exception as e:
                print(f"Warning: Error processing LLM response content: {e}")
                import traceback
                traceback.print_exc()
                # Keep the original parsed content string in the response if available
                if message_content_str:
                     resp["choices"][0]["message"]["content"] = message_content_str
                # Otherwise, the original raw resp dict is kept

        else: # Unexpected return from get_response
            print(f"Warning: Unexpected return value from get_response: {resp_raw}")
            resp = str(resp_raw) # Fallback


    # num_tokens = len(encoding.encode(prompt)) # Optional

    return {"prompt": prompt, "response": resp}


# --- Other functions remain unchanged ---


def get_config_recommendations_with_full_queries(
    dst_system, queries, temperature, retrieve_response: bool = False, system_specs=None
):

    prompt = (
        f"Recommend some configuration parameters for {dst_system} to optimize the system's performance. "
        f"Such parameters might include system-level configurations, like memory, query optimizer or query-level "
        f"configuration."
    )

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

    return {"prompt": prompt, "response": resp}


# Example call (ensure variables are populated):
# stats = {'total_sql_statements': 10, ...}
# specs = {'memory': '128GiB', 'cores': 64}
# result = get_config_recommendations_with_compression(
#     dst_system="POSTGRES",
#     relations={}, # Or actual dict
#     temperature=0.2,
#     retrieve_response=True,
#     workload_statistics=stats,
#     system_specs=specs,
#     indexes=True
# )
# print("\n--- FINAL RESULT ---")
# print(json.dumps(result, indent=2))
# print("------------------")
