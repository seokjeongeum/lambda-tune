import json
import os
import re  # Import the regular expression module

import tiktoken


# Assuming PostgresPlan is defined elsewhere correctly
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


# --- get_response function remains the same ---
def get_response(text: str, temperature: float):
    """
    Calls the Gemini API and returns a dictionary mimicking OpenAI's structure,
    or an error string.
    """
    try:
        # Configure API key if not already done globally
        # Make sure GOOGLE_API_KEY environment variable is set
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)

        # Define system instruction and model
        system_instruction = "You are a helpful Database Administrator."
        # DO NOT CHANGE THIS LINE
        gemini_model_name = "gemini-2.5-pro-exp-03-25"  # DO NOT CHANGE THIS LINE
        # DO NOT CHANGE THIS LINE
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
        # Check candidates and parts structure more robustly
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            # Return in OpenAI-like format
            return {
                "choices": [
                    {
                        "message": {
                            # Extract text from the first part
                            "content": response.candidates[0]
                            .content.parts[0]
                            .text,
                        }
                    }
                ]
            }
        else:
            # Handle failure/blocking cases
            finish_reason = (
                response.candidates[0].finish_reason
                if response.candidates
                and hasattr(response.candidates[0], "finish_reason")
                else "Unknown"
            )
            safety_feedback = (
                response.prompt_feedback
                if hasattr(response, "prompt_feedback")
                else "None"
            )
            # Try to get safety ratings if available
            if (
                hasattr(response, "candidates")
                and response.candidates
                and hasattr(response.candidates[0], "safety_ratings")
            ):
                safety_feedback = f"{safety_feedback}, SafetyRatings: {response.candidates[0].safety_ratings}"

            print(
                f"Warning: Gemini response did not contain expected content structure. Finish Reason: {finish_reason}, Safety Feedback: {safety_feedback}"
            )
            # Try to get any available text even if structure is off
            candidate_content = "No content found"
            try:
                if (
                    response.candidates
                    and response.candidates[0].content
                    and response.candidates[0].content.parts
                ):
                    candidate_content = response.candidates[0].content.parts[0].text
                elif (
                    hasattr(response, "text") and response.text
                ):  # Fallback to .text if it exists
                    candidate_content = response.text
            except Exception:
                pass  # Ignore errors trying to get partial content

            print(
                f"Raw Response (if available): {response}"
            )  # Log the raw response for debugging
            return f"Error: Gemini generation failed, was blocked, or response format unexpected. Reason: {finish_reason}. Content: '{candidate_content}'"

    except ValueError as ve:
        # Check specifically for API key issues which raise ValueError
        if "API_KEY" in str(ve):
            print(f"Gemini API Key Error: {ve}")
            return f"Error: {ve}"
        # Handle other ValueErrors (potentially malformed requests or prompt issues)
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
        f"The commands should primarily be for configuration settings (e.g., `ALTER SYSTEM SET parameter = value`) or creating indexes (`CREATE INDEX`). "
        f"Do not include any SQL comments (`--` or `/* */`) in the command strings. "
        # *** MODIFIED LINE: Be specific about ADD PRIMARY KEY ***
        f"**Crucially, do not include commands that add primary key constraints (e.g., `ALTER TABLE ... ADD PRIMARY KEY ...` or `ALTER TABLE ... ADD CONSTRAINT ... PRIMARY KEY ...`).** "
        f'Do **not** wrap individual commands in their own JSON objects (e.g., do not use {{"command": "..."}}).'
    )


# --- remove_sql_comments function remains the same ---
def remove_sql_comments(sql_command: str) -> str:
    """Removes single-line and multi-line SQL comments."""
    # Remove multi-line comments /* ... */ (non-greedy)
    sql_no_block_comments = re.sub(r"/\*.*?\*/", "", sql_command, flags=re.DOTALL)
    # Remove single-line comments -- ...
    sql_no_comments = re.sub(r"--.*", "", sql_no_block_comments)
    return sql_no_comments.strip()


# --- process_create_index_command function remains the same (includes UNIQUE removal) ---
def process_create_index_command(command: str) -> list[str]:
    """
    Processes a CREATE INDEX command according to the rules:
    - Converts 'CREATE UNIQUE INDEX' to 'CREATE INDEX'.
    - Removes 'IF NOT EXISTS'.
    - Removes 'CONCURRENTLY'.
    - Removes 'WHERE' clause (converts partial to full).
    - Removes 'USING <method>' clause (defaults to B-tree).
    - Splits multi-column index into multiple single-column indexes with derived names.
    - Returns a list of resulting command strings (usually 1, more for multi-column).
    """
    processed_commands = []
    original_command_for_log = command  # Keep original for logging

    # Remove comments first before checking structure
    command_no_comments = remove_sql_comments(command)
    # Handle empty string after comment removal
    if not command_no_comments:
        return []
    command_upper = command_no_comments.strip().upper()

    # Check if it's an index command AFTER removing comments
    # Use command_upper which reflects the comment-free version
    if not command_upper.startswith("CREATE INDEX") and not command_upper.startswith(
        "CREATE UNIQUE INDEX"
    ):
        # Ensure non-index commands end with a semicolon if they don't already
        final_cmd = command_no_comments  # Start with comment-free version
        if not final_cmd.endswith(";"):
            final_cmd += ";"
        return [final_cmd]

    # --- Initial Cleaning Steps (Comments already removed) ---
    current_command = (
        command_no_comments  # Start processing with the comment-free version
    )

    # *** Convert UNIQUE to non-unique ***
    command_no_unique = re.sub(
        r"CREATE\s+UNIQUE\s+INDEX", "CREATE INDEX", current_command, flags=re.IGNORECASE
    ).strip()
    if command_no_unique != current_command:
        print(f"Converted UNIQUE index to non-unique: {original_command_for_log}")
    current_command = command_no_unique  # Update current_command

    # 1. Remove IF NOT EXISTS (case-insensitive)
    command_no_ine = re.sub(
        r"\s+IF\s+NOT\s+EXISTS\s+", " ", current_command, flags=re.IGNORECASE
    ).strip()
    current_command = command_no_ine

    # 2. Remove CONCURRENTLY (case-insensitive)
    command_no_concurrently = re.sub(
        r"(INDEX)\s+CONCURRENTLY\s+", r"\1 ", current_command, flags=re.IGNORECASE
    ).strip()
    command_no_concurrently = re.sub(
        r"CREATE\s+CONCURRENTLY\s+(INDEX)",
        r"CREATE \1",
        command_no_concurrently,
        flags=re.IGNORECASE,
    ).strip()
    current_command = command_no_concurrently

    # 3. Remove WHERE clause (convert partial to full, case-insensitive)
    parts = re.split(r"\s+WHERE\s+", current_command, maxsplit=1, flags=re.IGNORECASE)
    command_no_where = parts[0].strip()
    current_command = command_no_where

    # 4. Remove USING clause (convert to default B-tree)
    command_cleaned = re.sub(
        r"\s+USING\s+\S+\s*(?=\()", " ", current_command, flags=re.IGNORECASE
    ).strip()
    if command_cleaned != current_command:
        print(f"Removed USING clause from: {original_command_for_log}")
    current_command = command_cleaned

    # 5. Parse index name, table, and columns from the *now fully cleaned* command
    match = re.match(
        r"CREATE\s+INDEX\s+(?P<name>\S+)\s+ON\s+(?P<table>\S+)\s*\((?P<cols>.*?)\)\s*;?",
        current_command,  # Use the final cleaned command
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        # Check if the original was likely an index command before failing
        if command_upper.startswith("CREATE INDEX") or command_upper.startswith(
            "CREATE UNIQUE INDEX"
        ):
            print(
                f"Warning: Could not parse final CREATE INDEX structure after cleaning: '{current_command}' from original '{original_command_for_log}'. Keeping command as is (after cleaning)."
            )
        # Fallback for commands that were never indexes or failed parsing
        if not current_command.endswith(";"):
            current_command += ";"
        return [current_command]  # Return the cleaned (but unparsed) command

    # --- Process columns ---
    index_name = match.group("name")
    table_name = match.group("table")
    cols_str = match.group("cols").strip()

    # Handle potential empty parenthesis '()'
    if not cols_str:
        print(
            f"Warning: Empty column list found in index: {original_command_for_log}. Discarding."
        )
        return []

    # Split columns, handling potential spaces and quotes within column names if needed
    # Basic split assumes simple column names or quoted names without commas inside
    columns = [c.strip() for c in re.split(r"\s*,\s*", cols_str) if c.strip()]

    if not columns:
        print(
            f"Warning: No columns found after parsing index: {original_command_for_log}. Discarding."
        )
        return []

    if len(columns) == 1:
        # Single-column index (fully cleaned, guaranteed non-unique)
        single_col_command = f"CREATE INDEX {index_name} ON {table_name} ({columns[0]})"
        if not single_col_command.endswith(";"):
            single_col_command += ";"
        processed_commands.append(single_col_command)
    else:
        # Multi-column index: Split (guaranteed non-unique)
        print(f"Splitting multi-column index: {original_command_for_log}")
        for i, col in enumerate(columns):
            # Sanitize column name for use in index name more carefully
            # Remove quotes, then sanitize
            sanitized_col = re.sub(
                r'^["\']|["\']$', "", col
            )  # Remove leading/trailing quotes
            col_name_part = re.sub(r"[^a-zA-Z0-9_]+", "_", sanitized_col).strip("_")
            if not col_name_part:
                col_name_part = f"col{i+1}"

            # Ensure derived name fits PostgreSQL limits (max 63 chars)
            base_name = f"{index_name}_col{i+1}"
            max_col_part_len = 63 - len(base_name) - 1  # -1 for the underscore
            if max_col_part_len < 1:  # Handle cases where base name is already too long
                # If base name is too long, just truncate it and don't add col part
                new_index_name = base_name[:63]
                print(
                    f"  Warning: Base index name '{base_name}' too long, truncating to '{new_index_name}'"
                )
            else:
                new_index_name = f"{base_name}_{col_name_part[:max_col_part_len]}"
                new_index_name = new_index_name[:63]  # Ensure final length

            # Use original column definition (potentially quoted) in the split command
            split_command = f"CREATE INDEX {new_index_name} ON {table_name} ({col})"
            if not split_command.endswith(";"):
                split_command += ";"
            processed_commands.append(split_command)
            print(f"  -> Generated: {split_command}")

    # Final check for empty strings in the result list just in case
    return [cmd for cmd in processed_commands if cmd]


# --- MODIFIED get_config_recommendations_with_compression ---
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
    data_definition_language: str = None,
):
    """
    Generate a prompt for recommendations, process the response to handle different
    JSON formats, transform indexes, remove comments, and filter ALTER TABLE commands. <<< UPDATED
    """
    # --- Prompt Building Logic (remains the same) ---
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

    # Add other prompt components (DDL, stats, relations, plans, etc.)
    if data_definition_language:
        prompt += "\nThe workload contains the following DDL statements:\n"
        prompt += f"{data_definition_language}\n"
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
        # Ensure table_access_frequency is serializable (e.g., dict)
        if isinstance(workload_statistics.get("table_access_frequency"), dict):
            try:
                prompt += "\nThe table access frequency is:\n" + json.dumps(
                    workload_statistics["table_access_frequency"], indent=2
                )
            except TypeError as json_err:
                print(f"Could not serialize table_access_frequency: {json_err}")
                prompt += f"\nTable access frequency data available but not shown due to serialization issue."
        else:
            prompt += f"\nTable access frequency: {workload_statistics.get('table_access_frequency', 'N/A')}"

    if query_plan and plans:
        prompt += "\n\nThe query plan is the following:\n"
        for plan_idx, plan_item in enumerate(plans):
            prompt += f"\n--- Plan {plan_idx + 1} ---\n"
            # Check if plan_item structure is as expected (e.g., tuple/list with plan obj)
            current_plan_obj = None
            if (
                isinstance(plan_item, (list, tuple))
                and len(plan_item) > 1
                and isinstance(plan_item[1], PostgresPlan)
            ):
                current_plan_obj = plan_item[1]
            elif isinstance(
                plan_item, PostgresPlan
            ):  # Handle case where plan is directly passed
                current_plan_obj = plan_item

            if current_plan_obj:
                # Safely access root and info if they exist
                plan_dict_to_serialize = None
                if hasattr(current_plan_obj, "root") and hasattr(
                    current_plan_obj.root, "info"
                ):
                    plan_dict_to_serialize = current_plan_obj.root.info
                else:
                    # Fallback if structure is slightly different but still PostgresPlan
                    if hasattr(current_plan_obj, "to_dict") and callable(
                        current_plan_obj.to_dict
                    ):
                        try:
                            plan_dict_to_serialize = current_plan_obj.to_dict()
                        except Exception as plan_err:
                            print(
                                f"Could not serialize plan object via to_dict(): {plan_err}"
                            )
                    elif hasattr(current_plan_obj, "__dict__"):  # Generic dict fallback
                        plan_dict_to_serialize = current_plan_obj.__dict__

                if plan_dict_to_serialize and isinstance(plan_dict_to_serialize, dict):
                    try:
                        prompt += (
                            json.dumps(plan_dict_to_serialize, indent=2, default=str)
                            + "\n"
                        )  # Add default=str for safety
                    except TypeError as json_err:
                        print(f"Could not JSON dump plan dict: {json_err}")
                        prompt += (
                            str(plan_dict_to_serialize) + "\n"
                        )  # Basic string fallback
                    except Exception as json_err:
                        print(f"Unexpected error JSON dumping plan dict: {json_err}")
                        prompt += (
                            str(plan_dict_to_serialize) + "\n"
                        )  # Basic string fallback
                else:  # If no suitable dict found
                    prompt += (
                        str(current_plan_obj) + "\n"
                    )  # Basic string fallback for the object
            # Handle cases where the item might be a plain dict
            elif isinstance(plan_item, dict):
                try:
                    prompt += json.dumps(plan_item, indent=2, default=str) + "\n"
                except Exception as json_err:
                    print(f"Could not JSON dump plan dict item: {json_err}")
                    prompt += str(plan_item) + "\n"
            else:  # Fallback for other unexpected structures
                prompt += str(plan_item) + "\n"

    elif join_conditions:
        if isinstance(join_conditions, dict):
            prompt += "\n\nJoin conditions found in the workload:\n" + "\n".join(
                f"{cond}: {join_conditions[cond]}" for cond in join_conditions
            )
        else:
            prompt += f"\n\nJoin conditions data (type {type(join_conditions)} not displayed correctly): {join_conditions}"

    if filters:
        if isinstance(filters, list):
            prompt += "\n\nFilters found in the workload:\n" + "\n".join(
                f"{cond}" for cond in filters
            )
        else:
            prompt += f"\n\nFilters data (type {type(filters)} not displayed correctly): {filters}"

    if internal_metrics:
        if isinstance(internal_metrics, dict):
            prompt += "\nThe internal metrics are the following:\n" + "\n".join(
                f"{metric}: {internal_metrics[metric]}" for metric in internal_metrics
            )
        else:
            prompt += f"\n\nInternal metrics data (type {type(internal_metrics)} not displayed correctly): {internal_metrics}"

    if system_specs:
        if isinstance(system_specs, dict):
            prompt += (
                "\nThe workload runs on a system with the following specs:\n"
                + "\n".join(f"{spec}: {system_specs[spec]}" for spec in system_specs)
            )
        else:
            prompt += f"\n\nSystem specs data (type {type(system_specs)} not displayed correctly): {system_specs}"

    if hints:
        prompt += f"\nHints: {hints}"

    prompt += "\n\n" + output_format()  # Add the format instructions at the end

    print("--- PROMPT ---")
    print(prompt)
    print("--------------")

    resp = None

    if retrieve_response:
        resp_raw = get_response(prompt, temperature=temperature)

        # Handle error string from get_response
        if isinstance(resp_raw, str) and resp_raw.startswith("Error:"):
            print(f"LLM call failed: {resp_raw}")
            resp = resp_raw  # Return the error string as the response
        # Handle successful dictionary response from get_response
        elif (
            isinstance(resp_raw, dict)
            and "choices" in resp_raw
            and resp_raw["choices"]
            and isinstance(resp_raw["choices"][0], dict)
            and "message" in resp_raw["choices"][0]
            and isinstance(resp_raw["choices"][0]["message"], dict)
            and "content" in resp_raw["choices"][0]["message"]
            and isinstance(resp_raw["choices"][0]["message"]["content"], str)
        ):
            resp = resp_raw  # Start with the raw structure
            processed_correctly = False  # Flag to track if processing succeeded
            message_content_str = ""  # Initialize for broader scope in error handling
            try:
                message_content_str = resp["choices"][0]["message"]["content"]
                # Clean potential markdown fences before parsing
                message_content_str = re.sub(
                    r"^```(?:json)?\s*",
                    "",
                    message_content_str,
                    flags=re.MULTILINE | re.IGNORECASE,
                )
                message_content_str = re.sub(
                    r"\s*```$", "", message_content_str, flags=re.MULTILINE
                ).strip()

                # Handle potential empty string after cleaning fences
                if not message_content_str:
                    raise json.JSONDecodeError(
                        "Response content is empty after cleaning.", "", 0
                    )

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
                    # Check if list items are strings (simplest case)
                    if all(isinstance(item, str) for item in parsed_content):
                        print("Detected format: List of strings [...]")
                        original_commands = parsed_content
                    # Check if list items are dicts with 'command' key
                    elif all(
                        isinstance(item, dict) and "command" in item
                        for item in parsed_content
                    ):
                        print("Detected format: List of dicts [{'command': ...}, ...]")
                        original_commands = [
                            item["command"]
                            for item in parsed_content
                            if isinstance(
                                item.get("command"), str
                            )  # Ensure command value is string
                        ]
                    # Check if list items are dicts with 'recommendations' key (nested list)
                    elif all(
                        isinstance(item, dict) and "recommendations" in item
                        for item in parsed_content
                    ):
                        print(
                            "Detected format: List containing {'recommendations': [...]}"
                        )
                        original_commands = []
                        for outer_item in parsed_content:
                            recs = outer_item.get("recommendations", [])
                            if isinstance(recs, list):
                                original_commands.extend(
                                    [
                                        item["command"]
                                        for item in recs
                                        if isinstance(item, dict)
                                        and isinstance(item.get("command"), str)
                                    ]
                                )
                    else:
                        print(
                            "Warning: Detected list format, but content structure is unrecognized or mixed."
                        )

                # Check for direct {'recommendations': [...]} format
                elif (
                    isinstance(parsed_content, dict)
                    and "recommendations" in parsed_content
                    and isinstance(parsed_content["recommendations"], list)
                    and all(
                        isinstance(item, dict) and "command" in item
                        for item in parsed_content["recommendations"]
                    )
                ):
                    print("Detected format: {'recommendations': [{'command':...}]}")
                    original_commands = [
                        item["command"]
                        for item in parsed_content["recommendations"]
                        # Add type check for item and command value
                        if isinstance(item, dict)
                        and isinstance(item.get("command"), str)
                    ]
                else:
                    print(
                        f"Warning: LLM response JSON is not in any expected command format. Parsed type: {type(parsed_content)}"
                    )

                # --- Process extracted commands if found ---
                if original_commands is not None and isinstance(
                    original_commands, list
                ):
                    processed_commands_final = []
                    skipped_alter_commands = 0
                    for cmd_idx, cmd in enumerate(original_commands):
                        if not isinstance(cmd, str):
                            print(
                                f"Warning: Skipping non-string item at index {cmd_idx} in commands list: {cmd}"
                            )
                            continue

                        # *** ADDED FILTER: Skip ALTER TABLE commands ***
                        cmd_stripped_upper = cmd.strip().upper()
                        if cmd_stripped_upper.startswith("ALTER TABLE"):
                            print(f"Filtering out ALTER TABLE command: {cmd}")
                            skipped_alter_commands += 1
                            continue  # Skip this command

                        # Process command (handles CREATE INDEX transformation and keeps others)
                        # remove_sql_comments is called inside process_create_index_command
                        resulting_cmds = process_create_index_command(
                            cmd
                        )  # Returns a list
                        processed_commands_final.extend(resulting_cmds)

                    # Final filtering for empty strings that might result from comment-only lines
                    processed_commands_final = [
                        c for c in processed_commands_final if c and c.strip()
                    ]

                    # Rebuild JSON content in the TARGET format {"commands": [...]}
                    final_content_dict = {"commands": processed_commands_final}
                    final_content_string = json.dumps(final_content_dict, indent=2)

                    # Update the response dictionary content to the standard format
                    resp["choices"][0]["message"]["content"] = final_content_string
                    processed_correctly = True  # Mark as successfully processed
                    print(
                        "\n--- STANDARDIZED & PROCESSED LLM CONTENT (Comments Removed, ALTER TABLE Filtered) ---"
                    )
                    print(final_content_string)
                    if skipped_alter_commands > 0:
                        print(
                            f"(Skipped {skipped_alter_commands} ALTER TABLE commands)"
                        )
                    print(
                        "-------------------------------------------------------------"
                    )

                else:  # No valid commands extracted or original_commands was not a list
                    print(
                        "Warning: Could not extract a valid list of commands from the received JSON structure."
                    )
                    # Keep the original parsed string if processing wasn't possible
                    resp["choices"][0]["message"]["content"] = message_content_str

                # If processing failed or structure was wrong, keep original JSON string
                if not processed_correctly:
                    resp["choices"][0]["message"]["content"] = message_content_str
                    print(
                        "\n--- KEPT ORIGINAL (UNPROCESSABLE or NO COMMANDS) LLM JSON CONTENT ---"
                    )
                    print(message_content_str)
                    print(
                        "---------------------------------------------------------------------"
                    )

            except json.JSONDecodeError as json_err:
                print(
                    f"Critical Warning: LLM response content was not valid JSON. Cannot process commands. Error: {json_err}. Raw content:"
                )
                print(message_content_str)
                # Keep the original NON-JSON string in the response
                resp["choices"][0]["message"]["content"] = message_content_str

            except Exception as e:
                print(f"Warning: Error processing LLM response content: {e}")
                import traceback

                traceback.print_exc()
                # Attempt to keep the original parsed content string in the response if available
                if "message_content_str" in locals() and message_content_str:
                    resp["choices"][0]["message"]["content"] = message_content_str
                # Otherwise, the original raw resp dict structure might be kept if the error was elsewhere

        else:  # Unexpected return from get_response or invalid structure
            print(
                f"Warning: Unexpected return value or structure from get_response: {resp_raw}"
            )
            # Try to salvage a string representation if possible
            if (
                isinstance(resp_raw, dict)
                and "choices" in resp_raw
                and resp_raw["choices"]
            ):
                try:
                    resp = str(resp_raw["choices"][0]["message"]["content"])
                except (KeyError, IndexError, TypeError):
                    resp = str(resp_raw)  # Fallback to string of whole dict
            else:
                resp = str(resp_raw)  # Fallback to basic string

    # num_tokens = len(encoding.encode(prompt)) # Optional

    # Ensure the final return value for 'response' is either the processed dict or an error string
    if isinstance(resp, dict) and "choices" in resp:  # Looks like success
        pass  # Keep the dict
    elif isinstance(resp, str):  # Looks like an error string or fallback string
        pass  # Keep the string
    else:  # Unexpected type for resp
        print(
            f"Warning: Final 'resp' object is of unexpected type {type(resp)}. Converting to string."
        )
        resp = str(resp)  # Convert to string as a final safety net

    return {"prompt": prompt, "response": resp}


# --- get_config_recommendations_with_full_queries remains the same ---
# (Though it also calls get_response and might benefit from similar error handling/JSON parsing logic)
def get_config_recommendations_with_full_queries(
    dst_system, queries, temperature, retrieve_response: bool = False, system_specs=None
):

    prompt = (
        f"Recommend some configuration parameters for {dst_system} to optimize the system's performance. "
        f"Such parameters might include system-level configurations, like memory, query optimizer or query-level "
        f"configuration."
    )

    # Assuming we always want index recommendations in this specific function variant
    prompt += "Include index recommendations (CREATE INDEX)."
    # else:
    #    prompt += "Do not include index recommendations."

    if queries:
        prompt += f"\nThe queries are the following\n"
        for query in queries:
            prompt += f"{query}\n"  # Assuming queries are strings

    if system_specs:
        prompt += f"\nThe workload runs on a system with the following specs:"
        if isinstance(system_specs, dict):
            for spec, value in system_specs.items():
                prompt += f"\n{spec}: {value}"
        else:
            prompt += f"\nSystem spec data provided but not in expected dict format: {system_specs}"

    prompt += "\n\n" + output_format()

    # print(prompt)
    try:
        num_tokens = len(encoding.encode(prompt))
        print(f"Prompt token count: {num_tokens}")
    except Exception as enc_err:
        print(f"Could not calculate token count: {enc_err}")

    final_response_content = None

    if retrieve_response:
        resp_raw = get_response(prompt, temperature=temperature)

        # Process the response similarly to the other function
        if isinstance(resp_raw, str) and resp_raw.startswith("Error:"):
            print(f"LLM call failed: {resp_raw}")
            final_response_content = resp_raw  # Keep error string
        elif (
            isinstance(resp_raw, dict) and "choices" in resp_raw and resp_raw["choices"]
        ):
            try:
                # Extract, clean, parse, filter, and reformat JSON
                message_content_str = resp_raw["choices"][0]["message"]["content"]
                message_content_str = re.sub(
                    r"^```(?:json)?\s*",
                    "",
                    message_content_str,
                    flags=re.MULTILINE | re.IGNORECASE,
                )
                message_content_str = re.sub(
                    r"\s*```$", "", message_content_str, flags=re.MULTILINE
                ).strip()

                if not message_content_str:
                    raise json.JSONDecodeError(
                        "Response content is empty after cleaning.", "", 0
                    )

                parsed_content = json.loads(message_content_str)
                original_commands = None

                # Detect command format (simplified check here, adapt if needed)
                if (
                    isinstance(parsed_content, dict)
                    and "commands" in parsed_content
                    and isinstance(parsed_content["commands"], list)
                ):
                    original_commands = parsed_content["commands"]
                elif isinstance(parsed_content, list) and all(
                    isinstance(item, str) for item in parsed_content
                ):
                    original_commands = parsed_content
                # Add more format detection if necessary based on observed LLM outputs

                if original_commands is not None and isinstance(
                    original_commands, list
                ):
                    processed_commands_final = []
                    skipped_alter_commands = 0
                    for cmd in original_commands:
                        if not isinstance(cmd, str):
                            continue
                        cmd_stripped_upper = cmd.strip().upper()
                        if cmd_stripped_upper.startswith("ALTER TABLE"):
                            print(f"Filtering out ALTER TABLE command: {cmd}")
                            skipped_alter_commands += 1
                            continue
                        # Assuming CREATE INDEX commands need the same processing
                        if cmd_stripped_upper.startswith(
                            "CREATE INDEX"
                        ) or cmd_stripped_upper.startswith("CREATE UNIQUE INDEX"):
                            resulting_cmds = process_create_index_command(cmd)
                            processed_commands_final.extend(resulting_cmds)
                        else:  # Keep other commands after cleaning comments
                            cmd_no_comments = remove_sql_comments(cmd)
                            if cmd_no_comments:  # Add if not empty
                                if not cmd_no_comments.endswith(";"):
                                    cmd_no_comments += ";"
                                processed_commands_final.append(cmd_no_comments)

                    processed_commands_final = [
                        c for c in processed_commands_final if c and c.strip()
                    ]
                    final_content_dict = {"commands": processed_commands_final}
                    final_response_content = json.dumps(
                        final_content_dict, indent=2
                    )  # Store the final JSON string
                    print("\n--- Processed LLM Content (Full Queries) ---")
                    print(final_response_content)
                    if skipped_alter_commands > 0:
                        print(
                            f"(Skipped {skipped_alter_commands} ALTER TABLE commands)"
                        )
                    print("-------------------------------------------")
                else:
                    print(
                        "Warning: Could not extract valid command list (Full Queries)."
                    )
                    final_response_content = (
                        message_content_str  # Keep original JSON string
                    )

            except json.JSONDecodeError as json_err:
                print(
                    f"Critical Warning: Invalid JSON received (Full Queries). Error: {json_err}. Raw content:"
                )
                print(
                    message_content_str
                    if "message_content_str" in locals()
                    else "Content unavailable"
                )
                final_response_content = (
                    message_content_str
                    if "message_content_str" in locals()
                    else f"Error: Invalid JSON received - {json_err}"
                )
            except Exception as e:
                print(f"Error processing response (Full Queries): {e}")
                final_response_content = (
                    message_content_str
                    if "message_content_str" in locals()
                    else f"Error processing response: {e}"
                )
        else:
            print(f"Unexpected response from get_response (Full Queries): {resp_raw}")
            final_response_content = str(resp_raw)  # Fallback

    # The original function structure tried to json.loads(str(resp)), which is problematic.
    # We now return the processed JSON *string* or an error string directly in final_response_content.
    # The calling code needs to handle this potentially being a JSON string or an error message.
    # Let's adjust the return structure slightly to match the other function better.
    # We return the dict structure, and 'response' key will hold either the dict from get_response (if processed)
    # or the error string / fallback string.

    final_return_resp = None
    if isinstance(final_response_content, str) and final_response_content.startswith(
        '{"commands":'
    ):
        # If it looks like our processed JSON, put it back into the dict structure
        try:
            # We need to mimic the original resp_raw structure if successful
            final_return_resp = {
                "choices": [{"message": {"content": final_response_content}}]
            }
        except (
            Exception
        ):  # Should not happen if final_response_content is valid JSON string
            final_return_resp = (
                final_response_content  # Fallback if constructing dict fails
            )
    else:
        # Keep it as a string (error or original unprocessed content)
        final_return_resp = final_response_content

    return {"prompt": prompt, "response": final_return_resp}
