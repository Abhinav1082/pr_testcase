"""
LLM prompt templates for OPA5/QUnit test generation.
"""

SYSTEM_PROMPT = """You are an expert SAP UI5 test engineer. Your task is to generate OPA5 integration tests and QUnit unit tests for SAP Fiori applications.

You MUST follow these rules:
1. Generate valid JavaScript test code using OPA5 and QUnit frameworks.
2. Tests must be self-contained and runnable within the SAPUI5 test infrastructure.
3. Use proper sap.ui.require/sap.ui.define module loading.
4. For controller logic changes, generate QUnit unit tests.
5. For view/fragment XML changes, generate OPA5 integration tests that verify UI behavior.
6. Follow SAP Fiori testing best practices and naming conventions.
7. Include meaningful assertion messages.
8. Do NOT generate tests for trivial changes (e.g., comments, whitespace).

Output format: Return a JSON array where each element has:
- "file_name": The test file name (e.g., "MainController.generated.test.js")
- "test_code": The complete test file content as a string
- "description": Brief description of what the test validates

Return ONLY the JSON array, no markdown fences or extra text."""

USER_PROMPT_TEMPLATE = """Generate OPA5/QUnit tests for the following changes in a SAP Fiori application.

## PR Information
- **Title**: {pr_title}
- **Description**: {pr_description}

## Changed Files

{changed_files_section}

## Existing Project Context
{project_context}

Generate comprehensive tests that validate the behavior introduced or modified by these changes. Focus on:
- Verifying new functionality works correctly
- Testing edge cases and error handling
- Ensuring UI elements render properly (for view changes)
- Validating data binding and model interactions
"""

CHANGED_FILE_TEMPLATE = """### File: `{file_path}` (Change type: {change_type})

**Full file content:**
```
{full_content}
```

**Diff (changes made in this PR):**
```diff
{diff}
```
"""

QUnit_TEST_EXAMPLE = """
// Example QUnit test structure for reference:
sap.ui.define([
    "sap/ui/base/ManagedObject",
    "your/namespace/controller/Main.controller"
], function (ManagedObject, MainController) {
    "use strict";

    QUnit.module("Main Controller Tests", {
        beforeEach: function () {
            this.oController = new MainController();
        },
        afterEach: function () {
            this.oController.destroy();
        }
    });

    QUnit.test("Should initialize model correctly", function (assert) {
        // Arrange & Act
        this.oController.onInit();
        // Assert
        assert.ok(this.oController.getView().getModel(), "Model should be set");
    });
});
"""

OPA5_TEST_EXAMPLE = """
// Example OPA5 test structure for reference:
sap.ui.define([
    "sap/ui/test/opaQunit",
    "your/namespace/test/integration/pages/Main"
], function (opaTest) {
    "use strict";

    QUnit.module("Main View Integration Tests");

    opaTest("Should display the main page", function (Given, When, Then) {
        // Arrangements
        Given.iStartMyApp();
        // Actions
        When.onTheMainPage.iLookAtTheScreen();
        // Assertions
        Then.onTheMainPage.iShouldSeeTheTitle();
        // Cleanup
        Then.iTeardownMyApp();
    });
});
"""


def build_test_generation_prompt(pr_info, project_context: str = "") -> list[dict]:
    """
    Build the messages list for the LLM chat completion call.

    Args:
        pr_info: PRInfo dataclass with PR metadata and changed files
        project_context: Additional context about the project structure

    Returns:
        List of message dicts with role and content keys
    """
    # Build the changed files section
    changed_files_section = ""
    for f in pr_info.changed_files:
        changed_files_section += CHANGED_FILE_TEMPLATE.format(
            file_path=f.path,
            change_type=f.change_type,
            full_content=f.full_content[:3000],  # Truncate large files
            diff=f.diff[:2000],
        )

    # Build user prompt
    user_content = USER_PROMPT_TEMPLATE.format(
        pr_title=pr_info.title,
        pr_description=pr_info.description or "No description provided.",
        changed_files_section=changed_files_section,
        project_context=project_context or "No additional context available.",
    )

    # Add examples for better output quality
    user_content += "\n\n## Reference Examples\n"
    user_content += QUnit_TEST_EXAMPLE
    user_content += OPA5_TEST_EXAMPLE

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    return messages
