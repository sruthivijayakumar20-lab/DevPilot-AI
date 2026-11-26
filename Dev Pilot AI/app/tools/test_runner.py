import re
import subprocess
import sys
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Repository workspace
WORKSPACE = (PROJECT_ROOT / "workspace").resolve()

# Maximum test execution time
TEST_TIMEOUT = 120

# Maximum output returned to the agent
MAX_OUTPUT_LENGTH = 12000


def run_project_tests(test_framework: str) -> dict:
    """
    Run project tests using an approved test framework.

    Supported frameworks:
    - pytest
    - unittest

    Tests are executed only inside the configured workspace.
    Arbitrary terminal commands are not permitted.
    """

    if not WORKSPACE.exists() or not WORKSPACE.is_dir():
        return {
            "status": "ERROR",
            "message": "Workspace directory does not exist.",
        }

    # Only allow predefined test commands.
    allowed_commands = {
        "pytest": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ],
        "unittest": [
            sys.executable,
            "-m",
            "unittest",
            "discover",
        ],
    }

    if not isinstance(test_framework, str):
        return {
            "status": "ERROR",
            "message": "Test framework must be a string.",
        }

    test_framework = test_framework.strip().lower()

    if test_framework not in allowed_commands:
        return {
            "status": "ERROR",
            "error_type": "UNSUPPORTED_FRAMEWORK",
            "message": (
                "Unsupported test framework. "
                "Use pytest or unittest."
            ),
        }

    command = allowed_commands[test_framework]

    try:
        result = subprocess.run(
            command,
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT,
            shell=False,
            check=False,
        )

        output = (
            (result.stdout or "")
            + "\n"
            + (result.stderr or "")
        ).strip()

        # Handle pytest results.
        if test_framework == "pytest":

            if result.returncode == 0:
                status = "PASSED"

            elif result.returncode == 1:
                status = "FAILED"

            elif result.returncode == 5:
                status = "NO_TESTS_FOUND"

            else:
                status = "ERROR"

        # Handle unittest results.
        else:

            # unittest can return exit code 0 even when
            # it discovers zero tests.
            no_tests_found = re.search(
                r"Ran\s+0\s+tests?",
                output,
                re.IGNORECASE,
            )

            if no_tests_found:
                status = "NO_TESTS_FOUND"

            elif result.returncode == 0:
                status = "PASSED"

            elif result.returncode == 1:
                status = "FAILED"

            else:
                status = "ERROR"

        return {
            "status": status,
            "framework": test_framework,
            "exit_code": result.returncode,
            "output": output[:MAX_OUTPUT_LENGTH],
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "ERROR",
            "error_type": "TIMEOUT",
            "framework": test_framework,
            "message": (
                f"Test execution exceeded {TEST_TIMEOUT} seconds."
            ),
        }

    except Exception as error:
        return {
            "status": "ERROR",
            "error_type": "EXECUTION_ERROR",
            "framework": test_framework,
            "message": str(error),
        }


if __name__ == "__main__":
    import json

    result = run_project_tests("pytest")
    print(json.dumps(result, indent=4))
