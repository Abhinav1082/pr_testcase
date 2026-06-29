"""
Run OPA5/QUnit tests and collect results.
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failures: list[dict] = field(default_factory=list)
    raw_output: str = ""
    success: bool = False


def _find_project_root(repo_root: str) -> str:
    """
    Find the Fiori project root (directory containing package.json).
    Handles monorepo structures by looking for the package.json closest
    to a webapp/ folder.
    """
    # First check if package.json is at repo root
    if os.path.isfile(os.path.join(repo_root, "package.json")):
        return repo_root

    # Search for package.json near webapp/ directories
    for root, dirs, files in os.walk(repo_root):
        if "node_modules" in root or ".git" in root:
            continue
        if "package.json" in files and os.path.isdir(os.path.join(root, "webapp")):
            return root

    return repo_root


def _install_dependencies(project_root: str) -> bool:
    """Install Node.js dependencies."""
    package_lock = os.path.join(project_root, "package-lock.json")
    cmd = ["npm", "ci"] if os.path.isfile(package_lock) else ["npm", "install"]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            logger.warning(f"npm install warnings: {result.stderr[:500]}")
        return True
    except subprocess.TimeoutExpired:
        logger.error("npm install timed out after 300 seconds.")
        return False
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def _parse_test_output(output: str) -> TestResult:
    """
    Parse test output to extract results.
    Supports Karma JSON reporter and basic QUnit TAP output.
    """
    result = TestResult(raw_output=output)

    # Try parsing as Karma JSON output
    try:
        # Look for JSON summary line in output
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("{") and "success" in line:
                data = json.loads(line)
                result.total = data.get("total", 0)
                result.passed = data.get("success", 0)
                result.failed = data.get("failed", 0)
                result.success = result.failed == 0
                return result
    except (json.JSONDecodeError, KeyError):
        pass

    # Try parsing TAP output format
    total = 0
    passed = 0
    failed = 0
    failures = []

    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("ok "):
            passed += 1
            total += 1
        elif line.startswith("not ok "):
            failed += 1
            total += 1
            failures.append({"message": line})
        elif line.startswith("1.."):
            try:
                total = int(line[3:])
            except ValueError:
                pass

    if total > 0:
        result.total = total
        result.passed = passed
        result.failed = failed
        result.failures = failures
        result.success = failed == 0
        return result

    # Fallback: look for common patterns in output
    # "X tests completed" / "X failures"
    import re

    completed_match = re.search(r"(\d+)\s+tests?\s+completed", output)
    failed_match = re.search(r"(\d+)\s+(?:failures?|failed)", output)

    if completed_match:
        result.total = int(completed_match.group(1))
        result.passed = result.total
    if failed_match:
        result.failed = int(failed_match.group(1))
        result.passed = result.total - result.failed

    result.success = result.failed == 0 and result.total > 0
    return result


def run_tests(repo_root: str, settings: dict) -> TestResult:
    """
    Run the project's test suite and return results.

    Args:
        repo_root: Path to the repository root
        settings: Configuration settings dict

    Returns:
        TestResult with test execution outcome
    """
    project_root = _find_project_root(repo_root)
    logger.info(f"Project root identified: {project_root}")

    # Install dependencies
    if not _install_dependencies(project_root):
        return TestResult(
            raw_output="Failed to install dependencies",
            success=False,
        )

    # Determine test command
    package_json_path = os.path.join(project_root, "package.json")
    test_cmd = ["npm", "test"]

    if os.path.isfile(package_json_path):
        try:
            with open(package_json_path, "r") as f:
                pkg = json.load(f)
            scripts = pkg.get("scripts", {})
            # Use the basic test command (Karma will use the testsuite which now
            # includes the generated tests page)
            if "test" in scripts:
                test_cmd = ["npm", "test"]
            else:
                logger.warning("No test script found in package.json")
                return TestResult(
                    raw_output="No test script found in package.json",
                    success=False,
                )
        except (json.JSONDecodeError, IOError):
            pass

    # Run tests
    logger.info(f"Running tests with command: {' '.join(test_cmd)}")
    try:
        result = subprocess.run(
            " ".join(test_cmd),
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600,
        )
        combined_output = result.stdout + "\n" + result.stderr
        test_result = _parse_test_output(combined_output)

        # If parsing couldn't determine results, use exit code
        if test_result.total == 0:
            test_result.success = result.returncode == 0
            test_result.raw_output = combined_output[-3000:]  # Last 3000 chars

        return test_result

    except subprocess.TimeoutExpired:
        logger.error("Test execution timed out after 600 seconds.")
        return TestResult(
            raw_output="Test execution timed out after 600 seconds.",
            success=False,
        )
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return TestResult(
            raw_output=str(e),
            success=False,
        )
