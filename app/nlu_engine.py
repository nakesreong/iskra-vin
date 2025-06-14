# app/nlu_engine.py
"""Natural language understanding using a local LLM via Ollama.

This module loads configuration and LLM instructions from the ``configs``
directory and exposes two main functions.  ``get_structured_nlu_from_text``
parses user text into intents and entities validated with Pydantic, while
``generate_natural_response`` produces a user-facing reply based on an action
result.  It is used by the core engine and tests for handling conversational
input.
"""

import yaml
import requests
import os
import json
from pathlib import Path
from typing import Optional, Any, Dict

from .config_loader import load_settings
from pydantic import BaseModel, ValidationError

# --- Pydantic Models for NLU JSON Validation ---


class EntitiesModel(BaseModel):
    target_device: Optional[str] = None
    action: Optional[str] = None
    location: Optional[str] = None
    # Specific fields for light settings, used with action: "setting"
    # For brightness percentage (0-100)
    brightness_pct: Optional[int] = None
    # For "warm", "cool", "natural"
    color_temp_qualitative: Optional[str] = None
    color_temp_kelvin: Optional[int] = None  # For specific Kelvin values
    # Generic value, can be used if no specific field above applies,
    # or for simple qualitative temperature if action is set_color_temperature (legacy, try to avoid)
    value: Optional[Any] = None
    expression: Optional[str] = None
    sensor_type: Optional[str] = None


class NluResponseModel(BaseModel):
    intent: str
    entities: Optional[EntitiesModel] = None


# --- Configuration and LLM Instructions Loading ---
CONFIG_DATA = None
LLM_INSTRUCTIONS_DATA = None

try:
    CONFIG_DATA = load_settings()
    if "ollama" not in CONFIG_DATA:
        raise ValueError("Section 'ollama' not found in configs/settings.yaml")
    print("NLU_Engine: Main configuration (settings.yaml) loaded successfully.")

    current_dir_nlu = Path(__file__).resolve().parent
    project_root_nlu = current_dir_nlu.parent

    instructions_path_nlu = project_root_nlu / "configs" / "llm_instructions.yaml"
    with instructions_path_nlu.open("r", encoding="utf-8") as f:
        LLM_INSTRUCTIONS_DATA = yaml.safe_load(f)

    if (
        not LLM_INSTRUCTIONS_DATA
        or "intent_extraction_instruction" not in LLM_INSTRUCTIONS_DATA
        or "response_generation_instruction_simple" not in LLM_INSTRUCTIONS_DATA
    ):
        raise ValueError(
            "Key instructions ('intent_extraction_instruction' or 'response_generation_instruction_simple') not found in configs/llm_instructions.yaml"
        )
    print("NLU_Engine: LLM instructions (llm_instructions.yaml) loaded successfully.")

except FileNotFoundError as fnf_err:
    print(f"NLU_Engine Error: Configuration or instructions file not found: {fnf_err}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
except (yaml.YAMLError, ValueError) as val_yaml_err:
    print(f"NLU_Engine Error: Error in configuration or instructions file: {val_yaml_err}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
except Exception as e:
    print(f"NLU_Engine Error: Unexpected error during configuration/instructions loading: {e}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
# --- End of Loading ---


def get_structured_nlu_from_text(user_text: str) -> dict:
    if not CONFIG_DATA or not LLM_INSTRUCTIONS_DATA:
        return {
            "error": "NLU_Engine: LLM configuration or instructions not loaded.",
            "intent": "config_error",
            "entities": {},
        }

    ollama_url = CONFIG_DATA.get("ollama", {}).get("base_url")
    model_name = CONFIG_DATA.get("ollama", {}).get("default_model")

    intent_extraction_instruction = LLM_INSTRUCTIONS_DATA.get("intent_extraction_instruction", "")
    examples = LLM_INSTRUCTIONS_DATA.get("examples", [])

    if not ollama_url or not model_name or not intent_extraction_instruction:
        return {
            "error": "NLU_Engine: Ollama URL, model name, or intent extraction instruction not found in config.",
            "intent": "config_error",
            "entities": {},
        }

    api_endpoint = f"{ollama_url}/api/chat"
    messages = []
    if intent_extraction_instruction:
        messages.append({"role": "system", "content": intent_extraction_instruction})

    for example in examples:
        if example.get("user_query") and example.get("assistant_json"):
            messages.append({"role": "user", "content": example["user_query"]})
            messages.append({"role": "assistant", "content": str(example["assistant_json"]).strip()})

    messages.append({"role": "user", "content": user_text})

    payload = {"model": model_name, "messages": messages, "format": "json", "stream": False}
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine: Sending NLU request to Ollama (/api/chat) with model {model_name}.")
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("message") and isinstance(response_data["message"], dict) and "content" in response_data["message"]:
            raw_json_string = response_data["message"]["content"]
            print(f"NLU_Engine: Received JSON string from LLM for NLU: {raw_json_string}")
            try:
                clean_json_string = raw_json_string.strip()
                if clean_json_string.startswith("```json"):
                    clean_json_string = clean_json_string[7:]
                if clean_json_string.startswith("```"):
                    clean_json_string = clean_json_string[3:]
                if clean_json_string.endswith("```"):
                    clean_json_string = clean_json_string[:-3]
                clean_json_string = clean_json_string.strip()

                parsed_dict = json.loads(clean_json_string)

                try:
                    validated_nlu = NluResponseModel(**parsed_dict)
                    print("NLU_Engine: NLU JSON successfully parsed and VALIDATED by Pydantic.")
                    return validated_nlu.model_dump()
                except ValidationError as val_err:
                    error_details_list = val_err.errors()
                    print(f"NLU_Engine Error: LLM JSON FAILED Pydantic validation: {error_details_list}")
                    return {
                        "error": "NLU JSON validation error",
                        "details": error_details_list,
                        "raw_response": raw_json_string,
                        "intent": "nlu_validation_error",
                        "entities": {},
                    }

            except json.JSONDecodeError as json_err:
                print(f"NLU_Engine Error: Failed to parse JSON from LLM NLU response: {json_err}")
                print(f"NLU_Engine: Raw NLU string was: {raw_json_string}")
                return {
                    "error": "NLU JSON parsing error",
                    "raw_response": raw_json_string,
                    "intent": "nlu_parsing_error",
                    "entities": {},
                }
        else:
            print(f"NLU_Engine Error: Unexpected NLU response format from Ollama (/api/chat): {response_data}")
            return {
                "error": "Unexpected NLU response format from Ollama",
                "raw_response": str(response_data),
                "intent": "nlu_ollama_error",
                "entities": {},
            }

    except requests.exceptions.RequestException as e:
        print(f"NLU_Engine Network Error: {e}")
        return {"error": f"NLU_Engine Network error: {e}", "intent": "nlu_network_error", "entities": {}}
    except Exception as e:
        print(f"NLU_Engine Unexpected Error: {e}")
        import traceback

        traceback.print_exc()
        return {"error": f"NLU_Engine Unexpected error: {e}", "intent": "nlu_unexpected_error", "entities": {}}


def generate_natural_response(action_result: dict, user_query: str = None) -> str:
    # This function remains the same as in your last working version.
    # It uses 'response_generation_instruction_simple'.
    if not CONFIG_DATA or not LLM_INSTRUCTIONS_DATA:
        print("NLU_Engine Error (gen_resp): LLM configuration or instructions not loaded.")
        return "Sorry, my response generation module is currently unavailable (config missing)."

    ollama_url = CONFIG_DATA.get("ollama", {}).get("base_url")
    model_name = CONFIG_DATA.get("ollama", {}).get("default_model")

    response_gen_instruction = LLM_INSTRUCTIONS_DATA.get("response_generation_instruction_simple", "")

    if not ollama_url or not model_name or not response_gen_instruction:
        print("NLU_Engine Error (gen_resp): Ollama URL, model, or response generation instruction not found.")
        return "Sorry, I can't formulate a response right now (config issue)."

    context_lines = ["Information about the result to formulate a response for Iskra:"]
    # Adapt this part based on what your action_handlers (like device_control_handler) will return
    # For a 'setting' action, you might want to include which settings were applied.
    if "success" in action_result:
        context_lines.append(f"- Success: {action_result.get('success')}")
        details = action_result.get("message_for_user", action_result.get("details_or_error", action_result.get("error", "no details")))
        context_lines.append(f"- System Details: {details}")
        # Add more specific details if available in action_result for 'setting'
        if action_result.get("action_performed") == "setting":
            if action_result.get("brightness_pct_set") is not None:
                context_lines.append(f"- Brightness set to: {action_result.get('brightness_pct_set')}%")
            if action_result.get("color_temp_qualitative_set") is not None:
                context_lines.append(f"- Color temperature set to: {action_result.get('color_temp_qualitative_set')}")
            if action_result.get("color_temp_kelvin_set") is not None:
                context_lines.append(f"- Color temperature set to: {action_result.get('color_temp_kelvin_set')}K")
    else:
        # Fallback for non-action results
        context_lines.append(f"- Recognized Intent: {action_result.get('intent', 'unknown')}")
        if action_result.get("entities"):
            context_lines.append(f"- Recognized Parameters: {json.dumps(action_result.get('entities'), ensure_ascii=False)}")
        if action_result.get("raw_response"):
            context_lines.append(f"- Raw JSON from NLU: {action_result.get('raw_response')}")

    if user_query:
        context_lines.append(f'- Iskra\'s original request was: "{user_query}"')

    context_lines.append("\nPlease, Nox, now respond to Iskra based on this information, following the system instruction.")
    context_for_llm = "\n".join(context_lines)

    api_endpoint = f"{ollama_url}/api/chat"
    messages = [{"role": "system", "content": response_gen_instruction}, {"role": "user", "content": context_for_llm}]
    payload = {"model": model_name, "messages": messages, "stream": False}
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine (gen_resp): Sending response generation request to Ollama (/api/chat).")
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get("message") and isinstance(response_data["message"], dict) and "content" in response_data["message"]:
            natural_response = response_data["message"]["content"].strip()
            print(f"NLU_Engine (gen_resp): Received natural response from LLM: {natural_response}")
            return natural_response
        else:
            print(f"NLU_Engine Error (gen_resp): Unexpected response format from Ollama: {response_data}")
            return "Sorry, I received a strange response and can't voice it."
    except requests.exceptions.RequestException as e:
        print(f"NLU_Engine Network Error (gen_resp): {e}")
        return "Sorry, I'm having trouble connecting to my 'brain'. Please try again later."
    except Exception as e:
        print(f"NLU_Engine Unexpected Error (gen_resp): {e}")
        import traceback

        traceback.print_exc()
        return "Oops, something went wrong while I was trying to think of a reply."


