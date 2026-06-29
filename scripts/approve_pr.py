"""
Post PR comments and approve the PR if tests pass.
"""

import logging

from github import Github

from scripts.run_tests import TestResult

logger = logging.getLogger(__name__)

COMMENT_TAG = "<!-- auto-test-bot -->"


def _build_comment_body(
    test_result: TestResult,
    generated_files: list[str],
    pr_number: int,
) -> str:
    """Build the markdown comment body for PR reporting."""
    lines = [COMMENT_TAG]
    lines.append("## 🤖 Automated Test Generation Report\n")

    # Summary
    lines.append(f"**PR #{pr_number}** — Generated **{len(generated_files)}** test file(s)\n")

    if generated_files:
        lines.append("### Generated Test Files")
        for f in generated_files:
            lines.append(f"- `{f}`")
        lines.append("")

    # Test Results
    lines.append("### Test Results\n")
    if test_result.success:
        lines.append(
            f"✅ **All tests passed** — "
            f"{test_result.passed}/{test_result.total} tests succeeded"
        )
    else:
        lines.append(
            f"❌ **Tests failed** — "
            f"{test_result.passed} passed, {test_result.failed} failed "
            f"out of {test_result.total} total"
        )

        if test_result.failures:
            lines.append("\n<details><summary>Failure Details</summary>\n")
            for failure in test_result.failures[:10]:
                msg = failure.get("message", "Unknown failure")
                lines.append(f"- {msg}")
            lines.append("\n</details>")

        if test_result.raw_output and not test_result.failures:
            lines.append("\n<details><summary>Test Output (last 1500 chars)</summary>\n")
            lines.append("```")
            lines.append(test_result.raw_output[-1500:])
            lines.append("```")
            lines.append("\n</details>")

    # Footer
    lines.append("\n---")
    if test_result.success:
        lines.append("*✅ PR auto-approved — all generated tests passed.*")
    else:
        lines.append("*❌ PR not approved — please review test failures above.*")

    return "\n".join(lines)


def post_comment_and_approve(
    repo_name: str,
    pr_number: int,
    token: str,
    test_result: TestResult,
    generated_files: list[str],
) -> None:
    """
    Post a comment on the PR with test results. Approve the PR if tests pass.

    Args:
        repo_name: Full repository name (e.g., "org/repo")
        pr_number: Pull request number
        token: GitHub token
        test_result: Test execution results
        generated_files: List of generated test file paths
    """
    gh = Github(token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    comment_body = _build_comment_body(test_result, generated_files, pr_number)

    # Update existing bot comment if one exists, otherwise create new
    existing_comment = None
    for comment in pr.get_issue_comments():
        if COMMENT_TAG in (comment.body or ""):
            existing_comment = comment
            break

    if existing_comment:
        existing_comment.edit(comment_body)
        logger.info("Updated existing bot comment on PR.")
    else:
        pr.create_issue_comment(comment_body)
        logger.info("Posted new comment on PR.")

    # Approve PR if tests passed
    if test_result.success and generated_files:
        try:
            pr.create_review(
                body="All auto-generated tests passed. Approving PR.",
                event="APPROVE",
            )
            logger.info(f"PR #{pr_number} approved.")
        except Exception as e:
            logger.error(f"Failed to approve PR: {e}")
    else:
        logger.info("Tests did not pass or no tests generated. PR not approved.")
