"""
Generate OPA5/QUnit tests using SAP AI Core / Generative AI Hub.
"""

import json
import logging
import os
import re
from dataclasses import dataclass

from scripts.fetch_pr_diff import PRInfo
from scripts.prompts.test_generation import build_test_generation_prompt

logger = logging.getLogger(__name__)


@dataclass
class GeneratedTest:
    file_name: str
    test_code: str
    description: str


def _get_project_context(repo_root: str) -> str:
    """Gather project context from manifest.json and existing test structure."""
    context_parts = []

    # Try to find manifest.json
    for root, dirs, files in os.walk(repo_root):
        if "node_modules" in root or ".git" in root:
            continue
        if "manifest.json" in files:
            manifest_path = os.path.join(root, "manifest.json")
            try:
                with open(manifest_path, "r") as f:
                    manifest = json.load(f)
                # Extract routing info
                routing = manifest.get("sap.ui5", {}).get("routing", {})
                if routing:
                    context_parts.append(
                        f"Routing config from {manifest_path}:\n"
                        f"{json.dumps(routing, indent=2)[:1500]}"
                    )
                # Extract namespace
                app_id = manifest.get("sap.app", {}).get("id", "")
                if app_id:
                    context_parts.append(f"Application namespace: {app_id}")
            except (json.JSONDecodeError, IOError):
                pass

    # List existing test files for reference
    test_files = []
    for root, dirs, files in os.walk(repo_root):
        if "node_modules" in root or ".git" in root:
            continue
        if "test" in root:
            for f in files:
                if f.endswith((".js", ".ts")):
                    test_files.append(os.path.relpath(os.path.join(root, f), repo_root))

    if test_files:
        context_parts.append(
            f"Existing test files:\n" + "\n".join(f"- {t}" for t in test_files[:20])
        )

    return "\n\n".join(context_parts) if context_parts else ""


def _parse_llm_response(response_text: str) -> list[GeneratedTest]:
    """Parse the LLM response into structured test data."""
    # Try to extract JSON from the response
    # Handle cases where LLM wraps in markdown code fences
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = response_text.strip()

    try:
        tests_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Response text: {response_text[:500]}")
        return []

    if not isinstance(tests_data, list):
        tests_data = [tests_data]

    generated_tests = []
    for item in tests_data:
        if not isinstance(item, dict):
            continue
        file_name = item.get("file_name", "")
        test_code = item.get("test_code", "")
        description = item.get("description", "")

        if not file_name or not test_code:
            continue

        # Sanitize file_name to prevent path traversal
        file_name = os.path.basename(file_name)
        if not file_name.endswith(".js"):
            file_name += ".js"

        # Ensure the generated suffix is present
        if ".generated.test" not in file_name:
            base = file_name.replace(".test.js", "").replace(".js", "")
            file_name = f"{base}.generated.test.js"

        generated_tests.append(
            GeneratedTest(
                file_name=file_name,
                test_code=test_code,
                description=description,
            )
        )

    return generated_tests


def generate_tests(
    pr_info: PRInfo, repo_root: str, settings: dict
) -> list[GeneratedTest]:
    """
    Generate OPA5/QUnit tests for the changed files using SAP AI Core.

    Args:
        pr_info: PR metadata and changed files
        repo_root: Path to the repository root
        settings: Configuration settings dict

    Returns:
        List of GeneratedTest objects
    """
    if not pr_info.changed_files:
        logger.info("No Fiori-relevant files changed. Skipping test generation.")
        return []

    llm_config = settings.get("llm", {})
    model_name = llm_config.get("model_name", "gpt-4")
    max_tokens = llm_config.get("max_tokens", 4096)
    temperature = llm_config.get("temperature", 0.2)
    chunk_size = llm_config.get("chunk_size", 5)
    max_retries = llm_config.get("max_retries", 1)

    # Get project context
    project_context = _get_project_context(repo_root)

    # Process files in chunks if there are many
    all_tests = []
    for i in range(0, len(pr_info.changed_files), chunk_size):
        chunk = pr_info.changed_files[i : i + chunk_size]

        # Create a temporary PRInfo with just this chunk
        chunk_pr_info = PRInfo(
            number=pr_info.number,
            title=pr_info.title,
            description=pr_info.description,
            base_branch=pr_info.base_branch,
            head_branch=pr_info.head_branch,
            changed_files=chunk,
        )

        messages = build_test_generation_prompt(chunk_pr_info, project_context)

        # Call SAP AI Core with retry logic
        response_text = None
        for attempt in range(max_retries + 1):
            try:
                from gen_ai_hub.proxy.native.openai import chat

                response = chat.completions.create(
                    model_name=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                response_text = response.choices[0].message.content
                break
            except Exception as e:
                logger.warning(
                    f"LLM call attempt {attempt + 1} failed: {e}"
                )
                if attempt == max_retries:
                    logger.error("All LLM call attempts exhausted.")
                    return all_tests

        if response_text:
            tests = _parse_llm_response(response_text)
            all_tests.extend(tests)
            logger.info(
                f"Generated {len(tests)} tests for chunk {i // chunk_size + 1}"
            )

    return all_tests


def write_tests_to_disk(
    tests: list[GeneratedTest], repo_root: str, settings: dict
) -> list[str]:
    """
    Write generated test files to the project's test directory.

    Args:
        tests: List of GeneratedTest objects
        repo_root: Path to the repository root
        settings: Configuration settings dict

    Returns:
        List of written file paths (relative to repo_root)
    """
    test_dir_rel = settings.get("test_output", {}).get(
        "directory", "webapp/test/integration"
    )
    test_dir = os.path.join(repo_root, test_dir_rel)
    os.makedirs(test_dir, exist_ok=True)

    written_files = []
    for test in tests:
        file_path = os.path.join(test_dir, test.file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(test.test_code)
        rel_path = os.path.relpath(file_path, repo_root)
        written_files.append(rel_path)
        logger.info(f"Wrote test file: {rel_path}")

    return written_files
