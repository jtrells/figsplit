""" Wrapper to consume the MATLAB code exposed in the service url """

import logging
from typing import Optional, Tuple
from os import listdir, remove
from os.path import join
from urllib.request import urlretrieve
from zipfile import ZipFile
from requests import post
from requests.exceptions import ConnectTimeout


class FigSplitWrapper:
    """Wrapper"""

    def __init__(self, endpoint: str, pref_extensions: Optional[Tuple]):
        self.endpoint = endpoint
        self.url = f"{self.endpoint}/modified_uploader"
        self.extensions = (
            pref_extensions
            if pref_extensions is not None
            else (".jpg", ".png", ".jpeg", "bmp", "tif", ".tif")
        )

    def split(self, _folder_path: str) -> Tuple[int, int, int, bool]:
        """Split JPG, JPEG, PNG, BMP, and, TIF images inside the folder path"""
        figures = [x for x in listdir(_folder_path) if x.endswith(self.extensions)]

        num_figures = len(figures)
        num_processed = 0
        num_success = 0

        raised_internal_server_error = False
        for figure in figures:
            num_processed += 1
            figure_file = None
            try:
                figure_file = open(join(_folder_path, figure), "rb")
                files = {"file": figure_file}
                response = post(self.url, files=files, timeout=60)
                if response.status_code == 200:
                    self.download_splitted_content(_folder_path, response, figure)
                    num_success += 1
                else:
                    message = f"{_folder_path}-{figure} code {response.status_code}"
                    logging.error(message)
                    raised_internal_server_error = True
            except ConnectTimeout:
                message = f"{_folder_path}-{figure} timed-out:"
                logging.error(message, exc_info=True)
            except Exception:  # pylint: disable=broad-except
                message = f"{_folder_path}-{figure}:"
                logging.error(message, exc_info=True)
            finally:
                if figure_file:
                    figure_file.close()

        return num_figures, num_processed, num_success, raised_internal_server_error

    def download_splitted_content(self, _folder_path, _response, _figure_name):
        """Process response to get output"""
        html = _response.text.split("\n")
        for line in html:
            if "download" in line and self.endpoint in line:
                link_of_zip = line.split('href="')[1].split('" download')[0]
                zip_name = f"{_figure_name}.zip"
                zip_path = join(_folder_path, zip_name)
                urlretrieve(link_of_zip, zip_path)
                FigSplitWrapper.__unpackage_zip(_folder_path, zip_name)
                remove(zip_path)

    @staticmethod
    def __unpackage_zip(_folder_path, zip_file):
        path_to_zip = join(_folder_path, zip_file)
        # zip files have this format: *.jpg.zip
        zip_name = zip_file[:-8]
        with ZipFile(path_to_zip, "r") as zip_ref:
            zip_ref.extractall(join(_folder_path, zip_name))
