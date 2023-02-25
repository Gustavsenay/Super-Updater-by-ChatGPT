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
RESET = "\033[0m"

def update_repository(repo_path):
    try:
        subprocess.run(["git", "fetch"], cwd=repo_path, check=True)
        return "SUCCESS", repo_path
    except subprocess.CalledProcessError as e:
        return "ERROR", repo_path, str(e)
    except Exception as e:
        return "EXCEPTION", repo_path, str(e)

if __name__ == "__main__":
    extensions_folder = "extensions"

    # Find all subdirectories in extensions folder that contain a .git directory
    git_dirs = [os.path.join(extensions_folder, d) for d in os.listdir(extensions_folder) if os.path.isdir(os.path.join(extensions_folder, d, ".git"))]

    # Set the number of processes to use and divide the repositories into groups
    num_processes = multiprocessing.cpu_count()
    repo_groups = [git_dirs[i:i+num_processes] for i in range(0, len(git_dirs), num_processes)]

    # Create a lock to ensure that only one process updates a repository at a time
    lock = Lock()

    # Update each repository in parallel using multiprocessing
    print(f"{YELLOW}Updating Git repositories in parallel...{RESET}")
    start_time = time.time()
    with multiprocessing.Pool(processes=num_processes) as pool:
        results = []
        for i, group in enumerate(repo_groups):
            for repo in group:
                results.append(pool.apply_async(update_repository, (repo,)))
                print(f"\033[KUpdating repository {i*num_processes+1} to {(i+1)*num_processes}...\r",)
                 
                
                
            while not all(result.ready() for result in results):
                time.sleep(0.1)
            print("\033[K\033[1A\033[K", end="")
    end_time = time.time()

    # Print summary
    # Print summary
    print(f"\033[KUpdated {len(git_dirs)} Git repositories in {end_time - start_time:.2f} seconds.")
    num_success = 0
    num_skipped = 0
    successes = []
    errors = []
    exceptions = []
    skipped = []
    for result in results:
        status, repo_path, *message = result.get()
        if status == "SUCCESS":
            num_success += 1
            successes.append(os.path.basename(repo_path))
        elif status == "ERROR":
            errors.append(os.path.basename(repo_path))
            print(f"  \033[31mERROR\033[0m: {os.path.basename(repo_path)} - {message[0]}")
        elif status == "EXCEPTION":
            exceptions.append(os.path.basename(repo_path))
            print(f"  \033[33mEXCEPTION\033[0m: {os.path.basename(repo_path)} - {message[0]}")
        elif status == "SKIPPED":
            num_skipped += 1
            skipped.append(os.path.basename(repo_path))
            print(f"  \033[35mSKIPPED\033[0m: {os.path.basename(repo_path)}")

    # Print detailed report of successful updates
    print("Fetch report:")
    for success in successes:
        print(f"  \033[32mSUCCESS\033[0m: {success}")
    for skip in skipped:
        print(f"  \033[35mSKIPPED\033[0m: {skip}")
    for error in errors:
        print(f"  \033[31mERROR\033[0m: {error}")
    for exception in exceptions:
        print(f"  \033[33mEXCEPTION\033[0m: {exception}")

    # Print summary of updates and skipped folders
    if num_skipped > 0 and len(errors) > 0:
        print(f"\033[K{num_success} repositories updated successfully; {num_skipped} folders skipped; {len(errors)} errors.")
    elif num_skipped > 0:
        print(f"\033[K{num_success} repositories updated successfully; {num_skipped} folders skipped.")
    elif len(errors) > 0:
        print(f"\033[K{num_success} repositories updated successfully; {len(errors)} errors.")
    else:
        print(f"\033[K{num_success} repositories updated successfully.")
