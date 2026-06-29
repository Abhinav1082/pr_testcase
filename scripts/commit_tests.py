"""
Commit generated test files to the PR branch.
"""

import logging
import subprocess

logger = logging.getLogger(__name__)


def commit_tests(written_files: list[str], pr_number: int, repo_root: str) -> bool:
    """
    Stage, commit, and push generated test files to the PR branch.

    Git identity and remote auth must be configured before calling this
    (handled by the GitHub Actions workflow).

    Args:
        written_files: List of file paths (relative to repo_root) to commit
        pr_number: PR number for the commit message
        repo_root: Path to the repository root

    Returns:
        True if commit and push succeeded, False otherwise
    """
    if not written_files:
        logger.info("No test files to commit.")
        return False

    try:
        # Stage all generated test files
        for file_path in written_files:
            subprocess.run(
                ["git", "add", file_path],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )

        # Also stage any generated loader/suite files
        subprocess.run(
            ["git", "add", "--all", "webapp/test/"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

        # Check if there are staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            logger.info("No changes to commit (files may already exist).")
            return False

        # Commit
        commit_msg = f"chore: add auto-generated OPA5/QUnit tests for PR #{pr_number}"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

        # Push to the current branch
        subprocess.run(
            ["git", "push"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )

        logger.info(
            f"Committed and pushed {len(written_files)} test file(s) to PR branch."
        )
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e.stderr}")
        return False
