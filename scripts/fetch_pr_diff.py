"""
Fetch PR diff and changed file contents from GitHub.
"""

import fnmatch
import os
from dataclasses import dataclass, field

from github import Github


@dataclass
class ChangedFile:
    path: str
    diff: str
    full_content: str
    change_type: str  # "added", "modified", "removed", "renamed"


@dataclass
class PRInfo:
    number: int
    title: str
    description: str
    base_branch: str
    head_branch: str
    changed_files: list[ChangedFile] = field(default_factory=list)


FIORI_PATTERNS = [
    "*.controller.js",
    "*.controller.ts",
    "*.view.xml",
    "*.fragment.xml",
    "*/model/*.js",
    "*/model/*.ts",
    "*formatter.js",
    "*formatter.ts",
    "Component.js",
    "Component.ts",
]


def _matches_fiori_pattern(file_path: str) -> bool:
    """Check if a file path matches any Fiori-relevant pattern."""
    filename = os.path.basename(file_path)
    for pattern in FIORI_PATTERNS:
        if fnmatch.fnmatch(filename, pattern):
            return True
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def fetch_pr_diff(repo_name: str, pr_number: int, token: str) -> PRInfo:
    """
    Fetch PR metadata and changed files from GitHub.

    Args:
        repo_name: Full repository name (e.g., "org/repo")
        pr_number: Pull request number
        token: GitHub token for authentication

    Returns:
        PRInfo with metadata and list of changed Fiori-relevant files
    """
    gh = Github(token)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    pr_info = PRInfo(
        number=pr.number,
        title=pr.title,
        description=pr.body or "",
        base_branch=pr.base.ref,
        head_branch=pr.head.ref,
    )

    files = pr.get_files()

    for file in files:
        if not _matches_fiori_pattern(file.filename):
            continue

        # Skip deleted files — no tests to generate for them
        if file.status == "removed":
            continue

        # Fetch full file content from the PR head branch
        full_content = ""
        try:
            content_file = repo.get_contents(file.filename, ref=pr.head.sha)
            if content_file and not isinstance(content_file, list):
                full_content = content_file.decoded_content.decode("utf-8")
        except Exception:
            # File might not exist (edge case with renames)
            full_content = ""

        changed_file = ChangedFile(
            path=file.filename,
            diff=file.patch or "",
            full_content=full_content,
            change_type=file.status,
        )
        pr_info.changed_files.append(changed_file)

    return pr_info
