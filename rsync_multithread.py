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

    file_paths = [line.strip() for line in lines if line.strip() and not line.startswith('./') and not line.startswith('sending') and not line.startswith('total size') and not line.startswith('receiving')]

    if not file_paths:
        print("No files to transfer. Check the remote directory and rsync settings.")
        return False

    file_paths = [f"{remote_path}{path}" for path in file_paths]

    chunk_size = max(1, len(file_paths) // num_threads)
    for i in range(num_threads):
        with open(f"thread_{i}_files.txt", 'w') as chunk_file:
            chunk_file.writelines([f"{path}\n" for path in file_paths[i*chunk_size:(i+1)*chunk_size]])

    return True

def main(remote_path, local_path, dry_run_output):
    dry_run_command = f"rsync -avn {remote_path} {local_path} > {dry_run_output}"
    subprocess.run(dry_run_command, shell=True)

    with open(dry_run_output, 'r') as file:
        file_count = sum(1 for line in file if line.strip() and not line.startswith('./') and not line.startswith('sending') and not line.startswith('total size') and not line.startswith('receiving'))

    num_threads = 5 if file_count <= 20 else 10

    num_threads = min(num_threads, file_count) if file_count > 0 else 1

    if split_file_list(dry_run_output, num_threads, remote_path):
        threads = []
        for i in range(num_threads):
            with open(f"thread_{i}_files.txt", 'r') as f:
                file_list = [line.strip() for line in f.readlines() if line.strip()]
            if file_list:
                thread = threading.Thread(target=execute_rsync, args=(file_list, local_path))
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

if __name__ == "__main__":
    remote_path = 'root@node1:/mnt/pve/HDD1/dump/'
    local_path = '/Users/levi/Documents/tmp/'
    dry_run_output = '/Users/levi/Documents/chunk/output.txt'
    main(remote_path, local_path, dry_run_output)