import os
import time
import git
import multiprocessing
import subprocess
from multiprocessing import Lock

# ANSI escape codes for colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"

def update_repository(repo_path):
    try:
        repo = git.Repo(repo_path)
        remote_branch = repo.remote().refs[0]
        local_branch = repo.heads[0]

        if local_branch.commit == remote_branch.commit:
            return "UP-TO-DATE", repo_path

        repo.remote().fetch()
        local_branch.commit = remote_branch.commit
        return "SUCCESS", repo_path

    except git.exc.GitCommandError as e:
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
    print(f"{YELLOW}Super-Updater-by-ChatGP{RESET}") 
    
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
    num_skipped = 0
    successes = []
    up_to_date = []
    errors = []
    exceptions = []
    skipped = []
    for result in results:
        status, repo_path, *message = result.get()
        if status == "SUCCESS":
            num_success += 1
            successes.append(os.path.basename(repo_path))
        elif status == "UP-TO-DATE":
            num_success += 1
            up_to_date.append(os.path.basename(repo_path))
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
    print(f"{YELLOW}Git Fetch report:{RESET}")
    for success in successes:
        print(f"  \033[32mSUCCESS\033[0m: {success}")
    for up_to_date in up_to_date:
        print(f"  \033[36mUP-TO-DATE\033[0m: {up_to_date}")
    for skip in skipped:
        print(f"  \033[35mSKIPPED\033[0m: {skip}")
    for error in errors:
        print(f"  \033[31mERROR\033[0m: {error}")
    for exception in exceptions:
        print(f"  \033[33mEXCEPTION\033[0m: {exception}")
        
    print(f"{YELLOW}\033[KProcessed {len(git_dirs)} Git repositories in {end_time - start_time:.2f} seconds{RESET}")
