import subprocess
import threading
import os
import re

def execute_rsync(file_list, local_path):
    for file in file_list:
        rsync_command = f"rsync -avz {file} {local_path}"
        subprocess.run(rsync_command, shell=True)

def split_file_list(file_list_path, num_threads, remote_path):
    with open(file_list_path, 'r') as file:
        lines = file.readlines()

    file_paths = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line and not any(
            phrase in stripped_line for phrase in ["receiving file list", "sent", "total size", "./"]
        ):
            file_paths.append(stripped_line)

    if not file_paths:
        print("No files to transfer. Check the remote directory and rsync settings.")
        return False

    chunk_size = len(file_paths) // num_threads + (len(file_paths) % num_threads > 0)
    for i in range(num_threads):
        with open(f"thread_{i}_files.txt", 'w') as chunk_file:
            chunk_files = [f"{remote_path}{file_path}\n" for file_path in file_paths[i*chunk_size:(i+1)*chunk_size]]
            chunk_file.writelines(chunk_files)

    return True

def main(remote_path, local_path, dry_run_output, num_threads=10):
    dry_run_command = f"rsync -avn {remote_path} {local_path} > {dry_run_output}"
    subprocess.run(dry_run_command, shell=True)

    if not split_file_list(dry_run_output, num_threads, remote_path):
        return

    threads = []
    for i in range(num_threads):
        with open(f"thread_{i}_files.txt", 'r') as f:
            file_list = [line.strip() for line in f.readlines() if line.strip()]
        thread = threading.Thread(target=execute_rsync, args=(file_list, local_path))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main('root@node1:/mnt/pve/HDD1/dump/', '/Users/levi/Documents/tmp/', '/Users/levi/Documents/chunk/output.txt')
