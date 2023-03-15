import os
import time
import multiprocessing
import subprocess

# Constants
SUPER_UPDATER_NAME = "Super-Updater-by-ChatGPT"
PROJECT_NAME = os.path.basename(os.getcwd())
SLEEP_DURATION = 0.1
ERROR_LOG_FILE = "error_log.txt"

# ANSI escape codes for colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
RESET = "\033[0m"


def update_main_project():
    """
    Update the main project's Git repository.
    """
    print(f"{YELLOW}{SUPER_UPDATER_NAME}{RESET}")
    try:
        result = subprocess.run(["git", "fetch", "--dry-run"], check=True, capture_output=True, text=True)
        output = result.stderr.strip()

        if output:
            subprocess.run(["git", "fetch"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "pull"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_result(GREEN, f"{PROJECT_NAME} updated successfully.", RESET, "")
        else:
            print_result(BLUE, f"{PROJECT_NAME} is up to date.", RESET, "")

    except subprocess.CalledProcessError as e:
        print_result(RED, f"Error updating main project: ", RESET, f"{e}")
        log_message("ERROR", f"{PROJECT_NAME} update error: {e}")
    except Exception as e:
        print_result(YELLOW, f"Exception updating {PROJECT_NAME}: ", RESET, f"{e}")
        log_message("EXCEPTION", f"{PROJECT_NAME} update exception: {e}")


def update_extension_repository(repo_path):
    """
    Update a Git repository located at the specified path.

    :param repo_path: Path to the Git repository
    :return: A tuple containing the status and repository path, as well as an optional message
    """
    try:
        result = subprocess.run(["git", "fetch", "--dry-run"], cwd=repo_path, check=True, capture_output=True, text=True)
        output = result.stderr.strip()

        if output:
            subprocess.run(["git", "fetch"], cwd=repo_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "UPDATED", repo_path
        else:
            return "UP_TO_DATE", repo_path
    except subprocess.CalledProcessError as e:
        return "ERROR", repo_path, str(e)
    except Exception as e:
        return "EXCEPTION", repo_path, str(e)


def print_result(status_color, status, repo_name_color, repo_name):
    """
    Print a colored status message with an optional repository name.

    :param status_color: ANSI color code for the status text
    :param status: Status text to print
    :param repo_name_color: ANSI color code for the repository name
    :param repo_name: Repository name to print (optional)
    """
    print(f"{status_color}{status}{RESET} {repo_name_color}{repo_name}{RESET}")


def log_message(status, message):
    """
    Log a message with a status to the error log file.

    :param status: Status text (e.g., "ERROR", "EXCEPTION")
    :param message: Message to log
    """
    with open(ERROR_LOG_FILE, "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {status}: {message}\n")

def main():
    update_main_project()
    extensions_folder = "extensions"
    git_dirs = [os.path.join(extensions_folder, d) for d in os.listdir(extensions_folder) if os.path.isdir(os.path.join(extensions_folder, d, ".git"))]
    num_processes = multiprocessing.cpu_count()
    repo_groups = [git_dirs[i:i + num_processes] for i in range(0, len(git_dirs), num_processes)]

    start_time = time.time()

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = []
        for i, group in enumerate(repo_groups):
            for repo in group:
                results.append(pool.apply_async(update_extension_repository, (repo,)))
            print(f"\033[KUpdating repository {i * num_processes + 1} to {(i + 1) * num_processes}...\r")
            while not all(result.ready() for result in results):
                time.sleep(SLEEP_DURATION)
            print("\033[K\033[1A\033[K", end="")
    end_time = time.time()

    num_success = 0
    num_up_to_date = 0
    successes = []
    errors = []
    exceptions = []
    up_to_date = []

    for result in results:
        status, repo_path, *message = result.get()
        repo_name = os.path.basename(repo_path)
        if status == "UPDATED":
            num_success += 1
            successes.append(repo_name)
        elif status == "UP_TO_DATE":
            num_up_to_date += 1
            up_to_date.append(repo_name)
        elif status == "ERROR":
            errors.append(repo_name)
            error_message = f"{repo_name} - {message[0]}"
            print_result(RED, f"ERROR {repo_name} - {message[0]}")
            log_message("ERROR", error_message)
        elif status == "EXCEPTION":
            exceptions.append(repo_name)
            exception_message = f"{repo_name} - {message[0]}"
            print_result(YELLOW, f"EXCEPTION {repo_name} - {message[0]}")
            log_message("EXCEPTION", exception_message)

    print(f"{YELLOW}Fetch report:{RESET}")
    for repo_name in successes:
        print_result(GREEN, "UPDATED", RESET, repo_name)
    for repo_name in up_to_date:
        print_result(BLUE, "UP_TO_DATE", RESET, repo_name)
    for repo_name in errors:
        print_result(RED, "ERROR", RESET, repo_name)
    for repo_name in exceptions:
        print_result(YELLOW, "EXCEPTION", RESET, repo_name)

    print(f"{len(successes)} repositories updated successfully.")
    print(f"{len(errors)} repositories failed with errors.")
    print(f"{len(exceptions)} repositories encountered exceptions.")
    print(f"{len(up_to_date)} repositories already up to date.")
    print(f"\033[KUpdated {len(git_dirs)} Git repositories in {end_time - start_time:.2f} seconds.")
    
if __name__ == "__main__":
    main()
