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
            return f"Error: Gemini generation failed or was blocked. Reason: {finish_reason}"

    except ValueError as ve:
        # Catch errors like blocked prompts
        print(f"An error occurred during Gemini API call (ValueError): {ve}")
        try:  # Try to get more details
            prompt_feedback = getattr(ve, "prompt_feedback", None)
            if prompt_feedback:
                print(f"Prompt Feedback: {prompt_feedback}")
                return f"Error: Gemini call failed due to prompt content. Feedback: {prompt_feedback}"
        except Exception:
            pass
        return f"Error: {ve}"
    except Exception as e:
        # Catch other errors
        print(f"An unexpected error occurred during Gemini API call: {e}")
        return f"Error: {e}"


# --- Refined output_format ---
def output_format():
    format_schema = '{\n  "commands": ["SQL command 1", "SQL command 2", ...]\n}'
    return (
        f"Your response should strictly consist of a single, valid JSON object matching the following schema. "
        f"Do not include any text before or after the JSON object, including markdown fences (```json ... ```).\n\n"
        f"Schema:\n{format_schema}\n\n"
        f"Ensure each element in the 'commands' list is a string containing a complete SQL command. "
        f'Do **not** wrap individual commands in their own JSON objects (e.g., do not use {{"command": "..."}}).'
    )


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

    if not command_upper.startswith("CREATE INDEX"):
        return [command]  # Return original if not CREATE INDEX

    # --- Initial Cleaning Steps ---
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
    command_no_where = parts[0].strip()  # Keep the part before WHERE

    # 4. Remove USING clause (convert to default B-tree) - MODIFIED LOGIC
    # Regex matches 'USING <method>' that might appear before the column list '('
    command_cleaned = re.sub(
        r"\s+USING\s+\S+\s*(?=\()", " ", command_no_where, flags=re.IGNORECASE
    ).strip()
    # Log if a USING clause was removed
    if command_cleaned != command_no_where:
        print(f"Removed USING clause from: {original_command_for_log}")

    # 5. Parse index name, table, and columns from the *now fully cleaned* command
    match = re.match(
        # Simplified regex: no longer need to capture USING clause here
        r"CREATE\s+INDEX\s+(?P<name>\S+)\s+ON\s+(?P<table>\S+)\s*\((?P<cols>.*?)\)\s*;?",
        command_cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        # This might happen if the original command was malformed *after* cleaning
        print(
            f"Warning: Could not parse final CREATE INDEX structure: {command}. Keeping command as is (after cleaning)."
        )
        if not command_cleaned.endswith(";"):
            command_cleaned += ";"
        return [command_cleaned]

    # --- Process columns ---
    index_name = match.group("name")
    table_name = match.group("table")
    cols_str = match.group("cols").strip()

    # Split columns
    columns = [c.strip() for c in cols_str.split(",") if c.strip()]

    if not columns:
        print(f"Warning: No columns found after parsing index: {command}. Discarding.")
        return []

    if len(columns) == 1:
        # Single-column index (fully cleaned)
        single_col_command = f"CREATE INDEX {index_name} ON {table_name} ({columns[0]})"  # No USING clause
        if not single_col_command.endswith(";"):
            single_col_command += ";"
        processed_commands.append(single_col_command)
    else:
        # Multi-column index: Split
        print(f"Splitting multi-column index: {original_command_for_log}")
        for i, col in enumerate(columns):
            col_name_part = re.sub(r'["\'\s\(\)]', "", col)  # Basic cleaning
            new_index_name = f"{index_name}_col{i+1}_{col_name_part}"
            new_index_name = new_index_name[:63]  # Truncate if needed

            split_command = f"CREATE INDEX {new_index_name} ON {table_name} ({col})"  # No USING clause
            if not split_command.endswith(";"):
                split_command += ";"
            processed_commands.append(split_command)
            print(f"  -> Generated: {split_command}")

    return processed_commands


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
):
    """
    Generate a prompt for recommendations, process the response to transform indexes.
    """
    # ... (prompt building logic remains the same as your last version) ...
    if not indexes_only:
        prompt = (
            f"Recommend some configuration parameters for {dst_system} to optimize the system's performance. "
            f"Such parameters might include system-level configurations, like memory, query optimizer "
            f"hints (such as join strategies, scan costs, parallelism, etc), "
            f"or query-level configurations."
        )
        if indexes:
            prompt += " Include index recommendations (CREATE INDEX)."
        else:
            prompt += " Do not include index recommendations."
    else:
        prompt = f"Give me index recommendations for the following input workload for {dst_system}. The index names should be unique.\n"

    if workload_statistics:
        prompt += "\nThe workload statistics are the following:\n" + "\n".join(
            f"{stat}: {workload_statistics[stat]}" for stat in workload_statistics
        )
    if relations:
        prompt += (
            "\nThe relations and their occurrences in the workload are the following:\n"
            + "\n".join(f"{rel}, {relations[rel]}" for rel in relations)
        )
    elif workload_statistics and "table_access_frequency" in workload_statistics:
        prompt += "\nThe table access frequency is:\n" + json.dumps(
            workload_statistics["table_access_frequency"], indent=2
        )
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
                        prompt += (
                            json.dumps(plan_item[1].to_dict(), indent=2) + "\n"
                        )  # Assuming a to_dict() method
                    except Exception as plan_err:
                        print(f"Could not serialize plan object: {plan_err}")
                        prompt += str(plan_item[1]) + "\n"  # Basic string fallback
            # Handle cases where the second element might be a plain dict
            elif len(plan_item) > 1 and isinstance(plan_item[1], dict):
                prompt += json.dumps(plan_item[1], indent=2) + "\n"
            else:  # Fallback for other unexpected structures
                prompt += str(plan_item) + "\n"
    elif join_conditions:
        prompt += "\n\nJoin conditions found in the workload:\n" + "\n".join(
            f"{cond}: {join_conditions[cond]}" for cond in join_conditions
        )
    if filters:
        prompt += "\n\nFilters found in the workload:\n" + "\n".join(
            f"{cond}" for cond in filters
        )
    if internal_metrics:
        prompt += "\nThe internal metrics are the following:\n" + "\n".join(
            f"{metric}: {internal_metrics[metric]}" for metric in internal_metrics
        )
    if system_specs:
        prompt += (
            "\nThe workload runs on a system with the following specs:\n"
            + "\n".join(f"{spec}: {system_specs[spec]}" for spec in system_specs)
        )
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
            try:
                message_content_str = resp["choices"][0]["message"]["content"]
                parsed_content = json.loads(
                    message_content_str
                )  # Parse the JSON string

                if isinstance(parsed_content, dict) and "commands" in parsed_content:
                    original_commands = parsed_content.get("commands", [])
                    processed_commands_final = []  # Store final list of commands

                    if isinstance(original_commands, list):
                        for cmd in original_commands:
                            if not isinstance(cmd, str):
                                print(
                                    f"Warning: Skipping non-string item in commands list: {cmd}"
                                )
                                continue  # Skip non-string commands

                            # Process command (handles CREATE INDEX transformation and keeps others)
                            resulting_cmds = process_create_index_command(cmd)
                            processed_commands_final.extend(
                                resulting_cmds
                            )  # Add the list of results

                        # Rebuild JSON content with the processed commands
                        final_content_dict = {"commands": processed_commands_final}
                        final_content_string = json.dumps(final_content_dict, indent=2)
                        resp["choices"][0]["message"][
                            "content"
                        ] = final_content_string  # Update the response
                        print("\n--- PROCESSED LLM CONTENT (Removed USING clauses) ---")
                        print(final_content_string)
                        print("----------------------------------------------------")

                    else:  # 'commands' was not a list
                        print(
                            f"Warning: Expected 'commands' to be a list, got {type(original_commands)}. Keeping original content."
                        )
                        # resp remains the raw response

                else:  # Parsed JSON didn't have top-level 'commands' key
                    print(
                        "Warning: LLM response JSON did not contain 'commands' key. Keeping original content."
                    )
                    # resp remains the raw response

            except json.JSONDecodeError:
                print(
                    "Warning: LLM response content was not valid JSON. Cannot process commands. Raw content:"
                )
                print(message_content_str)
                # resp remains the raw response (containing the non-JSON string)
            except Exception as e:
                print(f"Warning: Error processing LLM response content: {e}")
                import traceback

                traceback.print_exc()  # Print stack trace for debugging
                # resp remains the raw response
        else:  # Unexpected return from get_response
            print(f"Warning: Unexpected return value from get_response: {resp_raw}")
            resp = str(resp_raw)  # Fallback

    # num_tokens = len(encoding.encode(prompt)) # Optional

    return {"prompt": prompt, "response": resp}


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
