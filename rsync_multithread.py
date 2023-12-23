import subprocess
import os
import time

def generate_file_list(remote_source_directory, local_target_directory):
    """
    Generates a list of files to copy
    """
    if not remote_source_directory.endswith('/'):
        remote_source_directory += '/'

    command = ["rsync", "-av", "--dry-run", "--itemize-changes", remote_source_directory, local_target_directory]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Rsync error: {err.decode().strip()}")

    # Filter filenames
    return [line.split()[-1] for line in out.decode().split('\n') if line.startswith(">f")]

def split_file_list(file_list, chunk_size=20):
    """
    Splits the file list into chunks.
    """
    for i in range(0, len(file_list), chunk_size):
        yield file_list[i:i + chunk_size]

def write_chunks_to_files(chunks, chunk_dir):
    """
    Writes each chunk of files to a separate file in the chunk directory.
    """
    chunk_file_paths = []
    for i, chunk in enumerate(chunks):
        chunk_file_path = os.path.join(chunk_dir, f"chunk_{i}.txt")
        with open(chunk_file_path, 'w') as f:
            f.writelines('\n'.join(chunk))
        chunk_file_paths.append(chunk_file_path)
    return chunk_file_paths

def copy_files(chunk_file, remote_source_directory, local_target_directory):
    """
    Copies files listed in a chunk file using rsync.
    """
    rsync_command = ["rsync", "-av", "--files-from=" + chunk_file, remote_source_directory, local_target_directory]
    try:
        subprocess.run(rsync_command, check=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Rsync process failed: {e.stderr.decode().strip()}")



def main(remote_source_directory, local_target_directory, chunk_directory):
    file_list = generate_file_list(remote_source_directory, local_target_directory)

    if not os.path.exists(chunk_directory):
        os.makedirs(chunk_directory)

    chunk_files = write_chunks_to_files(split_file_list(file_list), chunk_directory)

    for chunk_file in chunk_files:
        copy_files(chunk_file, remote_source_directory, local_target_directory)
        while is_rsync_running():
            time.sleep(1)

def is_rsync_running():
    """
    Checks if rsync is currently running.
    """
    try:
        subprocess.run(["pgrep", "-x", "rsync"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

if __name__ == "__main__":
    REMOTE_SOURCE_DIRECTORY = 'levi@nginx:/home/levi/data/'  
    LOCAL_TARGET_DIRECTORY = '/Users/levi/Documents/tmp/'  
    CHUNK_DIRECTORY = '/Users/levi/Documents/chunk/'  
    main(REMOTE_SOURCE_DIRECTORY, LOCAL_TARGET_DIRECTORY, CHUNK_DIRECTORY)
