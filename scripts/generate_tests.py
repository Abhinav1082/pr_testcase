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

    # Register generated tests in the test suite files
    _register_tests_in_suite(tests, repo_root, test_dir_rel)

    return written_files


def _register_tests_in_suite(
    tests: list[GeneratedTest], repo_root: str, test_dir_rel: str
) -> None:
    """
    Register generated test files in the appropriate test suite loader
    so Karma can discover and run them.

    Creates a dedicated loader file (generatedTests.qunit.js) that imports
    all generated test modules, and registers it in the main test suite HTML.
    """
    if not tests:
        return

    # Derive the UI5 module path prefix from manifest.json
    app_namespace = _get_app_namespace(repo_root)
    # Convert test_dir_rel (e.g., "webapp/test/integration") to module path
    # Strip "webapp/" prefix for module paths
    module_base = test_dir_rel.replace("webapp/", "").replace("/", "/")

    # Build the list of generated test module paths
    test_modules = []
    for test in tests:
        # Remove .js extension for sap.ui.require module path
        module_name = test.file_name.replace(".js", "")
        module_path = f"{app_namespace}/{module_base}/{module_name}"
        test_modules.append(module_path)

    # Create a dedicated generated tests loader file
    loader_content = _build_generated_tests_loader(test_modules)
    loader_path = os.path.join(repo_root, test_dir_rel, "generatedTests.qunit.js")
    with open(loader_path, "w", encoding="utf-8") as f:
        f.write(loader_content)
    logger.info(f"Created generated tests loader: {loader_path}")

    # Create the HTML file that Karma will use to run these tests
    loader_html_path = os.path.join(repo_root, test_dir_rel, "generatedTests.qunit.html")
    html_content = _build_generated_tests_html(app_namespace, module_base)
    with open(loader_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    logger.info(f"Created generated tests HTML: {loader_html_path}")

    # Update the main test suite to include the generated tests page
    _update_testsuite(repo_root, test_dir_rel)


def _get_app_namespace(repo_root: str) -> str:
    """Get the app namespace from manifest.json, converted to module path format."""
    for root, dirs, files in os.walk(repo_root):
        if "node_modules" in root or ".git" in root:
            continue
        if "manifest.json" in files:
            try:
                with open(os.path.join(root, "manifest.json"), "r") as f:
                    manifest = json.load(f)
                app_id = manifest.get("sap.app", {}).get("id", "")
                if app_id:
                    return app_id.replace(".", "/")
            except (json.JSONDecodeError, IOError):
                pass
    return "com/demo/fioriapp"


def _build_generated_tests_loader(test_modules: list[str]) -> str:
    """Build the JS loader file that imports all generated test modules."""
    modules_str = ",\n    ".join(f'"{m}"' for m in test_modules)
    return f'''sap.ui.require([
    {modules_str}
], function () {{
    "use strict";
    QUnit.start();
}});
'''


def _build_generated_tests_html(app_namespace: str, module_base: str) -> str:
    """Build the QUnit HTML page for running generated tests."""
    # Calculate relative path to webapp root from test directory
    depth = module_base.count("/") + 1
    relative_root = "/".join([".."] * depth)

    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Generated Tests - Auto PR Testing</title>
    <script
        id="sap-ui-bootstrap"
        src="https://sdk.openui5.org/resources/sap-ui-core.js"
        data-sap-ui-theme="sap_horizon"
        data-sap-ui-resourceroots=\'{{
            "{app_namespace.replace("/", ".")}": "{relative_root}/"
        }}\'
        data-sap-ui-async="true">
    </script>
    <link rel="stylesheet" type="text/css" href="https://sdk.openui5.org/resources/sap/ui/thirdparty/qunit-2.css">
    <script src="https://sdk.openui5.org/resources/sap/ui/thirdparty/qunit-2.js"></script>
    <script src="https://sdk.openui5.org/resources/sap/ui/qunit/qunit-junit.js"></script>
    <script src="generatedTests.qunit.js"></script>
</head>
<body>
    <div id="qunit"></div>
    <div id="qunit-fixture"></div>
</body>
</html>
'''


def _update_testsuite(repo_root: str, test_dir_rel: str) -> None:
    """Add the generated tests page to the main test suite if not already present."""
    testsuite_path = os.path.join(repo_root, "webapp", "test", "testsuite.qunit.html")
    if not os.path.isfile(testsuite_path):
        return

    with open(testsuite_path, "r") as f:
        content = f.read()

    # Check if generated tests page is already registered
    generated_page = f"{test_dir_rel.replace('webapp/', 'test/')}/generatedTests.qunit.html"
    if generated_page in content:
        return

    # Insert the generated tests page into the test suite
    insert_marker = 'return oSuite;'
    if insert_marker in content:
        new_line = f'            oSuite.addTestPage("{generated_page}");\n            '
        content = content.replace(insert_marker, new_line + insert_marker)
        with open(testsuite_path, "w") as f:
            f.write(content)
        logger.info(f"Registered generated tests in testsuite.qunit.html")
