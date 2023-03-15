import os
import time
import multiprocessing
import subprocess
from multiprocessing import Lock

# ANSI escape codes for colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

def update_repository(repo_path):
    try:
        # Check for updates
        result = subprocess.run(["git", "fetch", "--dry-run"], cwd=repo_path, check=True, capture_output=True, text=True)
        output = result.stderr.strip()

        if output:
            # Apply updates
            subprocess.run(["git", "fetch"], cwd=repo_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "SUCCESS", repo_path
        else:
            return "UP_TO_DATE", repo_path
    except subprocess.CalledProcessError as e:
        return "ERROR", repo_path, str(e)
    except Exception as e:
        return "EXCEPTION", repo_path, str(e)

def print_result(status, repo_name, message=None):
    if message:
        print(f"  {status} {repo_name} - {message}")
    else:
