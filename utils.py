import hashlib
import time
import pandas as pd
from multiprocessing import Pool, cpu_count


def sha256_hash(s: str) -> str:
    """Hash s to sha256"""
    return hashlib.sha256(s.encode()).hexdigest()

def worker(args):
    """
    Worker function for each process.

    :param args: A tuple of (start, end, target_hashes)
    :return: Dict mapping matched hashes to their corresponding trader_id
    """
    start, end, target_hashes = args
    local_found = {}

    for trader_id in range(start, end):
        hashed = sha256_hash(str(trader_id))
        if hashed in target_hashes:
            local_found[hashed] = trader_id

    return local_found

def chunkify(total: int, chunks: int):
    """
    Split a total range (e.g., 1 to 5 million) into approximately equal chunks.

    :param total: Total number of IDs (e.g., 5_000_000)
    :param chunks: Number of processes to use
    :return: List of (start, end) ranges for each process
    """
    step = total // chunks  # Determine the size of each chunk
    ranges = []

    for i in range(chunks):
        start = i * step + 1  # Start of the chunk (1-based index)
        if i == chunks - 1:
            # Last chunk goes up to the end to avoid losing data due to integer division
            end = total + 1
        else:
            end = (i + 1) * step + 1
        ranges.append((start, end))

    return ranges


# def find_trader_id_from_trader_hash_parallel(user_counts: int, processes: int = None):
#     """
#     Parallelized function to brute-force trader ID from hash.
#
#     :param user_counts: Max trader ID to try (e.g., 5_000_000)
#     :param processes: Number of processes to use (defaults to all CPUs)
#     """
#     start_time = time.time()
#
#     # Auto-detect number of CPU cores if not provided
#     processes = processes or cpu_count()
#
#     # Split the range of IDs to chunks for parallel processing
#     ranges = chunkify(user_counts, processes)
#
#     # Prepare arguments for each worker
#     args = [(start, end, hash_list) for start, end, in ranges]
#
#     founds = {}
#
#     # Launch worker pool
#     with Pool(processes=processes) as pool:
#         for partial_result in pool.map(worker, args):
#             founds.update(partial_result)
#
#     # Display results and timing
#     print(founds)
#     print(f'Run time: {time.time() - start_time:.2f}s | #processes: {processes}')


def match_hashes_parallel(hash_list, max_id=5_000_000, processes=None):
    """Use multiprocessing to reverse hashes to trader IDs."""
    processes = processes or cpu_count()
    ranges = chunkify(max_id, processes)
    args = [(start, end, set(hash_list)) for start, end in ranges]

    founds = {}
    with Pool(processes) as pool:
        for result in pool.map(worker, args):
            founds.update(result)
    return founds


def process_excel(input_filepath: str, sheet_name: str, column_name: str, output_filename: str, max_users_id: int = 5_000_000):
    """Main function: read Excel, find Trader IDs, and write result."""
    start_time = time.time()

    # Step 1: Read input Excel
    df = pd.read_excel(input_filepath, sheet_name=sheet_name)
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in the sheet.")

    # Step 2: Extract hashes and preserve order
    hash_list = df[column_name].astype(str).tolist()

    # Step 3: Match hashes to trader IDs
    found_map = match_hashes_parallel(hash_list, max_users_id)

    # Step 4: Create output DataFrame
    result_df = pd.DataFrame({
        'Trader Hash': hash_list,
        'Trader ID': [found_map.get(h, None) for h in hash_list]  # Preserve order
    })

    # Step 5: Write to Excel
    result_df.to_excel(output_filename, index=False)

    print(f"✅ Done! Output written to: {output_filename}")
    print(f"⏱️ Total time: {time.time() - start_time:.2f}s")


# Example usage
if __name__ == '__main__':

    input_excel_file = input('excel file path to read from: ') or "trader_hashes.xlsx"
    sheet_name = input('sheet name: ') or "Sheet1"
    column_name = input('Column name: ') or "Trader Hash"
    output_excel_file = input('excel file path to write to: ') or "trader_id_results.xlsx"

    process_excel(input_excel_file, sheet_name, column_name, output_excel_file)