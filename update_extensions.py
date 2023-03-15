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

def update_main_project():
    print(f"{YELLOW}Super-Updater-by-ChatGPT{RESET}")
    try:
        # Check for updates
        result = subprocess.run(["git", "fetch", "--dry-run"], check=True, capture_output=True, text=True)
        output = result.stderr.strip()

        if output:
            # Apply updates
            subprocess.run(["git", "fetch"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "pull"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{GREEN}Automatic1111's WebUI updated successfully.{RESET}")
        else:
            print(f"{BLUE}Automatic1111's WebUI is up to date.{RESET}")

    except subprocess.CalledProcessError as e:
        print(f"{RED}Error updating main project: {e}{RESET}")
        log_error("ERROR", f"Automatic1111's WebUI update error: {e}")
    except Exception as e:
        print(f"{YELLOW}Exception updating Automatic1111's WebUI: {e}{RESET}")
        log_error("EXCEPTION", f"Automatic1111's WebUI update exception: {e}")

def update_repository(repo_path):
    try:
        # Check for updates
        result = subprocess.run(["git", "fetch", "--dry-run"], cwd=repo_path, check=True, capture_output=True, text=True)
        output = result.stderr.strip()

        if output:
            # Apply updates
            subprocess.run(["git", "fetch"], cwd=repo_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "UPDATED", repo_path
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
        print(f"  {status} {repo_name}")

def log_error(status, message):
    with open("error_log.txt", "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {status}: {message}\n")

if __name__ == "__main__":
    update_main_project()
    extensions_folder = "extensions"

    # Find all subdirectories in extensions folder that contain a .git directory
    git_dirs = [os.path.join(extensions_folder, d) for d in os.listdir(extensions_folder) if os.path.isdir(os.path.join(extensions_folder, d, ".git"))]

    # Set the number of processes to use and divide the repositories into groups
    num_processes = multiprocessing.cpu_count()
    repo_groups = [git_dirs[i:i+num_processes] for i in range(0, len(git_dirs), num_processes)]

    # Create a lock to ensure that only one process updates a repository at a time
    lock = Lock()

    # Update each repository in parallel using multiprocessing
        
    start_time = time.time()

    with multiprocessing.Pool(processes=num_processes) as pool:
        results = []
        for i, group in enumerate(repo_groups):
            for repo in group:
                results.append(pool.apply_async(update_repository, (repo,)))
            print(f"\033[KUpdating repository {i*num_processes+1} to {(i+1)*num_processes}...\r")
            while not all(result.ready() for result in results):
                time.sleep(0.1)
            print("\033[K\033[1A\033[K", end="")
    end_time = time.time()

    # Print summary
    
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
            print_result(RED + "ERROR" + RESET, repo_name, message[0])
            log_error("ERROR", error_message)
        elif status == "EXCEPTION":
            exceptions.append(repo_name)
            exception_message = f"{repo_name} - {message[0]}"
            print_result(YELLOW + "EXCEPTION" + RESET, repo_name, message[0])
            log_error("EXCEPTION", exception_message)

    # Print fetch report
    print("Fetch report:")
    for repo_name in successes:
        print_result(GREEN + "UPDATED" + RESET, repo_name)
    for repo_name in up_to_date:
        print_result(BLUE + "UP_TO_DATE" + RESET, repo_name)
    for repo_name in errors:
        print_result(RED + "ERROR" + RESET, repo_name)
    for repo_name in exceptions:
        print_result(YELLOW + "EXCEPTION" + RESET, repo_name)


    print(f"{len(successes)} repositories updated successfully.")
    print(f"{len(errors)} repositories failed with errors.")
    print(f"{len(exceptions)} repositories encountered exceptions.")
    print(f"{len(up_to_date)} repositories already up to date.")
    print(f"\033[KUpdated {len(git_dirs)} Git repositories in {end_time - start_time:.2f} seconds.")
