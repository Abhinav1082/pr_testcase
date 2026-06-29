"""
Main orchestrator for the automated PR test generation pipeline.

This script is the entry point called by GitHub Actions. It chains:
1. Fetch PR diff
2. Generate tests via SAP AI Core
3. Write tests to project
4. Commit tests to PR branch
5. Run tests
6. Post results & approve/reject PR
"""

import logging
import os
import sys

import yaml

from scripts.approve_pr import post_comment_and_approve
from scripts.commit_tests import commit_tests
from scripts.fetch_pr_diff import fetch_pr_diff
from scripts.generate_tests import generate_tests, write_tests_to_disk
from scripts.run_tests import run_tests, TestResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def load_settings() -> dict:
    """Load configuration from settings.yaml."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "settings.yaml")
    config_path = os.path.abspath(config_path)

    if os.path.isfile(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def main():
    """Main pipeline orchestrator."""
    # Read environment variables (set by GitHub Actions)
    token = os.environ.get("GITHUB_TOKEN")
    pr_number = os.environ.get("PR_NUMBER")
    repo_name = os.environ.get("REPO_FULL_NAME")

    if not all([token, pr_number, repo_name]):
        logger.error(
            "Missing required environment variables: "
            "GITHUB_TOKEN, PR_NUMBER, REPO_FULL_NAME"
        )
        sys.exit(1)

    pr_number = int(pr_number)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    settings = load_settings()

    logger.info(f"Starting automated test pipeline for PR #{pr_number} in {repo_name}")

    # --- Phase 1: Fetch PR diff ---
    logger.info("Phase 1: Fetching PR diff...")
    try:
        pr_info = fetch_pr_diff(repo_name, pr_number, token)
    except Exception as e:
        logger.error(f"Failed to fetch PR diff: {e}")
        sys.exit(1)

    if not pr_info.changed_files:
        logger.info("No testable Fiori files changed. Posting skip comment.")
        skip_result = TestResult(success=True, total=0, passed=0, failed=0)
        post_comment_and_approve(
            repo_name, pr_number, token, skip_result, []
        )
        return

    logger.info(
        f"Found {len(pr_info.changed_files)} Fiori-relevant changed file(s): "
        + ", ".join(f.path for f in pr_info.changed_files)
    )

    # --- Phase 2: Generate tests ---
    logger.info("Phase 2: Generating tests via SAP AI Core...")
    try:
        generated_tests = generate_tests(pr_info, repo_root, settings)
    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        fail_result = TestResult(
            success=False, raw_output=f"Test generation error: {e}"
        )
        post_comment_and_approve(
            repo_name, pr_number, token, fail_result, []
        )
        sys.exit(1)

    if not generated_tests:
        logger.warning("LLM did not generate any tests.")
        no_tests_result = TestResult(
            success=False,
            raw_output="The AI model did not generate any test cases for this PR.",
        )
        post_comment_and_approve(
            repo_name, pr_number, token, no_tests_result, []
        )
        return

    logger.info(f"Generated {len(generated_tests)} test file(s).")

    # --- Phase 3: Write tests to disk ---
    logger.info("Phase 3: Writing tests to project...")
    written_files = write_tests_to_disk(generated_tests, repo_root, settings)
    logger.info(f"Wrote {len(written_files)} file(s): {written_files}")

    # --- Phase 4: Commit tests to PR branch ---
    logger.info("Phase 4: Committing tests to PR branch...")
    committed = commit_tests(written_files, pr_number, repo_root)
    if committed:
        logger.info("Tests committed and pushed to PR branch.")
    else:
        logger.info("No new commits needed (tests may already exist or commit failed).")

    # --- Phase 5: Run tests ---
    logger.info("Phase 5: Running tests...")
    test_result = run_tests(repo_root, settings)
    logger.info(
        f"Test results: {test_result.passed} passed, "
        f"{test_result.failed} failed, {test_result.total} total"
    )

    # --- Phase 6: Report results & approve/reject ---
    logger.info("Phase 6: Posting results and approval decision...")
    post_comment_and_approve(
        repo_name, pr_number, token, test_result, written_files
    )

    if test_result.success:
        logger.info("Pipeline completed successfully. PR approved.")
    else:
        logger.warning("Pipeline completed. Tests failed — PR not approved.")
        sys.exit(1)


if __name__ == "__main__":
    main()
