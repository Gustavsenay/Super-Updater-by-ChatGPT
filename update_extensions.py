import os
import subprocess
import time
import logging
from multiprocessing import Pool
import shutil

start_time = time.time()

EXTENSIONS_DIR = "extensions"

import logging
import os
import subprocess

# ANSI color codes
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
DEFAULT = "\033[0m"
SMALL = "\033[2m"
MONO = "\033[1m\033[37m"

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create console handler with no formatting
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(message)s"))
console_handler.flush = lambda: None  # disable handler buffering
logger.addHandler(console_handler)

def update_folder(folder):
    try:
        result = subprocess.run(["git", "status"], cwd=folder, check=True, capture_output=True, stdin=subprocess.DEVNULL)
        padding = ' ' + '-' * (48 - len(os.path.basename(folder))) + ' '
        if "Your branch is up to date" not in result.stdout.decode():
            logger.info(f"{YELLOW}Updating {os.path.basename(folder)}...{DEFAULT}")
            pull_result = subprocess.run(["git", "pull"], cwd=folder, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL)
            logger.info(pull_result.stdout.decode())
            return True
        else:
            logger.info(fr"{os.path.basename(folder)}{GREEN}{padding}Already up to date{DEFAULT}")
            return False
    except subprocess.CalledProcessError as error:
        logger.error(f"{os.path.basename(folder)}{RED}{padding}Error: {error.stderr.decode().strip()}{DEFAULT}")
        return False

        
def update_extensions(folder):
    if os.path.isdir(folder):
        if update_folder(folder):
            try:
                result = subprocess.run(["git", "log", "-1"], cwd=folder, check=True, capture_output=True)
                commit = result.stdout.decode().strip()
                return f"{os.path.basename(folder)}: {GREEN}{commit}{DEFAULT}"
            except subprocess.CalledProcessError as error:
                return f"{os.path.basename(folder)}: {RED}{error.stderr.decode().strip()}{DEFAULT}"
        else:
            return None

def update_extensions_parallel(extension_folders):
    with Pool(processes=os.cpu_count()) as pool:
        results = pool.map(update_extensions, extension_folders)
    updated_extensions = [folder for folder, result in zip(extension_folders, results) if result is not None and not result.startswith(f"{os.path.basename(folder)} - Already up to date")]
    results = [result if not result.startswith(f"{os.path.basename(folder)} - Already up to date") else f"{os.path.basename(folder)} ┃ {result}" for folder, result in zip(extension_folders, results) if result is not None]

    return "\n".join(results), updated_extensions

def main():
    logger.info(f"{YELLOW}UPDATING EVERYTHING{DEFAULT}".center(shutil.get_terminal_size().columns or 50, " "))
    main_folder = os.path.dirname(os.path.abspath(__file__))
    update_folder(main_folder)
    
    extensions_path = os.path.join(main_folder, EXTENSIONS_DIR)
    extension_folders = [os.path.join(extensions_path, folder) for folder in os.listdir(extensions_path)]
    results, updated_extensions = update_extensions_parallel(extension_folders)
    logger.info(f"{results}")
    logger.info(f"{YELLOW}UPDATING FINISHED{DEFAULT}".center(shutil.get_terminal_size().columns, " "))

    # Collect and print updating results
    if updated_extensions:
        logger.info(f"{'EXTENSION NAME'} | {'STATUS'.rjust(shutil.get_terminal_size().columns)}")
        for extension in updated_extensions:
            logger.info(extension)
    else:
        logger.info(f"{GREEN}No extensions updated")

    elapsed_time = time.time() - start_time
    logger.info(f"{YELLOW}time to update: {elapsed_time:.2f} seconds{DEFAULT}".center(shutil.get_terminal_size().columns, " "))
    logger.propagate = False  # prevent log messages from being propagated up the logger hierarchy


if __name__ == "__main__":
    main()