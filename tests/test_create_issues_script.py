import shutil
import subprocess
import sys


def test_create_github_issues_script_parses_and_runs_dryrun():
    pwsh = shutil.which("pwsh")
    if not pwsh:
        # No PowerShell Core available in the environment; skip the test
        import pytest

        pytest.skip("pwsh not available")
    # Run the script (dry-run) and ensure it exits 0
    completed = subprocess.run([pwsh, "-NoProfile", "-Command", ".\\scripts\\create_github_issues.ps1"], capture_output=True, text=True)
    assert completed.returncode == 0, f"Script failed: stdout={completed.stdout}\nstderr={completed.stderr}"
