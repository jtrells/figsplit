""" Wrapper to invoke figsplit """

import logging
import multiprocessing
from argparse import ArgumentParser
from pathlib import Path
from typing import List
from os import listdir

from figsplit.core.figsplit_wrapper import FigSplitWrapper


FIGSPLIT_URL = "https://www.eecis.udel.edu/~compbio/FigSplit"


def split(folder_path: Path, processed_file_path: Path):
    """Split function to call in parallel"""
    wrapper = FigSplitWrapper(FIGSPLIT_URL, pref_extensions=(".jpg"))
    num_figures, num_processed, num_success = wrapper.split(folder_path)
    with open(processed_file_path, "a", encoding="utf-8") as file:
        file.write(f"{folder_path.stem},{num_figures},{num_processed},{num_success}\n")


def read_processed_ids(filename: str) -> List[str]:
    """returns the ids stored in a log file"""
    try:
        with open(filename, "r", encoding="utf-8") as file:
            ids = file.read().splitlines()
        ids = [x.split(",")[0] for x in ids]
    except FileNotFoundError:
        print(f"{filename} file not yet created")
        ids = []
    return ids


def batch(iterable, size=256):
    """Create an iterable to process a long list in batches.
    Needed to process the data in batches and guarantee that we are not filling
    the memory with the data from processes that were already finished.
    """
    # https://stackoverflow.com/questions/8290397/how-to-split-an-iterable-in-constant-size-chunks
    len_iterable = len(iterable)
    for ndx in range(0, len_iterable, size):
        yield iterable[ndx : min(ndx + size, len_iterable)]


def main():
    """Split the figures based on a folder-wise organization"""
    parser = ArgumentParser(prog="figsplit", description="batch proc figsplit")
    parser.add_argument(
        "input_path", type=str, help="Folder containing the images to process"
    )
    parser.add_argument("--num_workers", type=int, default=10)
    args = parser.parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"input_path {input_path} does not exist")
        return

    log_path = input_path / "figsplit.log"
    logging.basicConfig(
        filename=log_path.resolve(),
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    processed_log = input_path / "processed_figsplit.log"

    processed_ids = read_processed_ids(processed_log.resolve())
    tentative_ids = [x for x in listdir(input_path) if ((input_path) / x).is_dir()]
    ids_to_process = list(set(tentative_ids).difference(set(processed_ids)))

    batch_size = 128
    items = [(input_path / el, processed_log) for el in ids_to_process]

    for data_batch in batch(items, size=batch_size):
        pool = multiprocessing.Pool()
        with multiprocessing.Pool(args.num_workers) as pool:
            pool.starmap(split, data_batch)
        pool.terminate()
