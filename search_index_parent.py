# search_index_parent

import fcntl
import fitz  # PyMuPDF
import logging
import os
import shutil
import sys
import time
from xml.sax.saxutils import escape

# Versioning
__version__ = "1.1.5"
# pyinstaller --onefile --name search_index_parent-V1.1.5 search_index_parent.py

# Global variables
log_file_path = ""
marker_log_file_path = ""
path_to_files = ""
processed_files = set()

# Toggle for testing
USE_HARD_CODED_PATHS = False
HARD_CODED_PATH_TO_FILES = r"E:\Testing Directory\Docs"

LOCK_FILE = "/tmp/search_index_parent.lock"  # Path to the lock file


def main(args):
    # lock_file = open(LOCK_FILE, 'w')
    try:
        # fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        initialize(args)
        txt_temp_path = create_temp_directory(path_to_files)
        load_processed_files(txt_temp_path)
        accumulated_index_file_path = os.path.join(path_to_files, "search_index.xml")

        # Check if file exists and has content; otherwise, initialize it.
        if not os.path.exists(accumulated_index_file_path) or os.stat(accumulated_index_file_path).st_size == 0:
            with open(accumulated_index_file_path, 'w', encoding='utf-8') as accumulated_writer:
                accumulated_writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
                accumulated_writer.write('<files>\n')
                traverse_main_folders(path_to_files, txt_temp_path, accumulated_writer)
                accumulated_writer.write('</files>\n')

        # Open in append mode to prevent overwriting
        with open(accumulated_index_file_path, 'a', encoding='utf-8') as accumulated_writer:
            traverse_main_folders(path_to_files, txt_temp_path, accumulated_writer)

        logging.info("All directories processed successfully.")

        # clean_up_temp_directory(txt_temp_path)

    except OSError as e:
        logging.error(f"Script is already running: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)

    finally:
        # fcntl.lockf(lock_file, fcntl.LOCK_UN)
        # lock_file.close()
        # This prompt will be shown regardless of whether an exception was raised
        input("Press Enter to close this window...")


def initialize(args):
    global path_to_files
    if USE_HARD_CODED_PATHS:
        # Hard-coded paths for testing
        path_to_files = HARD_CODED_PATH_TO_FILES
    else:
        path_to_files = os.getcwd()
    initialize_logging()
    logging.info(f"search_index_parent Version: {__version__}")


def initialize_logging():
    global log_file_path, marker_log_file_path
    log_file_path = os.path.join(path_to_files, "search_builder_processing_log.txt")
    marker_log_file_path = os.path.join(path_to_files, "processed_files_log.txt")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )


def get_path_tail(path):
    # This function returns the last two parts of the path
    parts = path.split(os.sep)

    # Exclude the filename if it exists
    if os.path.isfile(path):
        parts = parts[:-1]

    # Return the last two directory parts
    if len(parts) >= 2:
        return os.path.join(parts[-2], parts[-1])
    elif len(parts) == 1:
        return parts[0]
    return ""


def create_temp_directory(directory_path):
    txt_temp_path = os.path.join(directory_path, "txtTemp")
    os.makedirs(txt_temp_path, exist_ok=True)
    return txt_temp_path


def load_processed_files(txt_temp_path):
    global processed_files
    if os.path.exists(marker_log_file_path):
        with open(marker_log_file_path, 'r') as f:
            processed_files = {line.strip() for line in f}
    # logging.info(f"Loaded processed files: {processed_files}")


def traverse_main_folders(root_path, txt_temp_path, accumulated_writer):
    skip_folders = {"Airside Civil", "Demolition", "Garage", "Landside Civil"}
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if item in skip_folders:
            logging.info(f"Skipping directory due to filter: {item}")
            continue
        if os.path.isdir(item_path) and item != "txtTemp":
            logging.info(f"Processing directory: {item_path}")
            if item.lower() == "no classification":
                # Process NO CLASSIFICATION folder as root
                process_no_classification_folder(item_path, txt_temp_path, accumulated_writer)
            else:
                process_main_folder(item_path, txt_temp_path, accumulated_writer)


def process_main_folder(directory_path, txt_temp_path, accumulated_writer):
    # processed_files.clear()
    index_file_path = os.path.join(directory_path, "search_index.xml")
    needs_header = not os.path.exists(index_file_path) or os.stat(index_file_path).st_size == 0

    with open(index_file_path, 'a', encoding='utf-8') as writer:
        if needs_header:
            writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
            writer.write('<files>\n')

        traverse_and_process_directory(directory_path, txt_temp_path, writer)

        if needs_header:
            writer.write('</files>\n')

    logging.info(f"Created/Updated search index for {os.path.basename(directory_path)}")
    if needs_header:
        append_to_accumulated_index(index_file_path, accumulated_writer)


def process_no_classification_folder(directory_path, txt_temp_path, accumulated_writer):
    no_class_accumulated_path = os.path.join(directory_path, "search_index.xml")
    needs_header = not os.path.exists(no_class_accumulated_path) or os.stat(no_class_accumulated_path).st_size == 0

    with open(no_class_accumulated_path, 'a', encoding='utf-8') as no_class_accumulated_writer:
        if needs_header:
            no_class_accumulated_writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
            no_class_accumulated_writer.write('<files>\n')

        for sub_directory in os.listdir(directory_path):
            sub_directory_path = os.path.join(directory_path, sub_directory)
            if os.path.isdir(sub_directory_path):
                process_sub_folder(sub_directory_path, txt_temp_path, no_class_accumulated_writer,
                                   include_subdirectories=True)

        if needs_header:
            no_class_accumulated_writer.write('</files>\n')

        logging.info(f"Created/Updated search index for {os.path.basename(directory_path)} (NO CLASSIFICATION)")
        append_to_accumulated_index(no_class_accumulated_path, accumulated_writer)


def process_sub_folder(directory_path, txt_temp_path, accumulated_writer, include_subdirectories=False):
    # processed_files.clear()
    sub_index_file_path = os.path.join(directory_path, "search_index.xml")
    needs_header = not os.path.exists(sub_index_file_path) or os.stat(sub_index_file_path).st_size == 0

    with open(sub_index_file_path, 'a', encoding='utf-8') as sub_writer:
        if needs_header:
            sub_writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
            sub_writer.write('<files>\n')

        traverse_and_process_directory(directory_path, txt_temp_path, sub_writer, include_subdirectories)

        if needs_header:
            sub_writer.write('</files>\n')

    logging.info(f"Created/Updated search index for {os.path.basename(directory_path)}")
    if needs_header:
        append_to_accumulated_index(sub_index_file_path, accumulated_writer)


def append_to_accumulated_index(index_file_path, accumulated_writer):
    with open(index_file_path, 'r', encoding='utf-8') as reader:
        for line in reader:
            if line.strip() not in ('<?xml version="1.0" encoding="utf-8"?>', '<files>', '</files>'):
                accumulated_writer.write(line)


def traverse_and_process_directory(directory_path, txt_temp_path, writer, include_subdirectories=False):
    process_files_in_directory(directory_path, txt_temp_path, writer)
    for sub_directory in os.listdir(directory_path):
        sub_directory_path = os.path.join(directory_path, sub_directory)
        if os.path.isdir(sub_directory_path):
            if include_subdirectories:
                process_sub_folder(sub_directory_path, txt_temp_path, writer, include_subdirectories=True)
            else:
                traverse_and_process_directory(sub_directory_path, txt_temp_path, writer)


def process_files_in_directory(directory_path, txt_temp_path, writer):
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        marker_file_path = os.path.join(txt_temp_path, file_name + '.processed')

        # if file_name.lower() == "search_index.xml" or os.path.exists(marker_file_path):
        if file_name.lower() == "search_index.xml" or file_name in processed_files:
            logging.info(f"Skipping File: {file_name}")
            continue  # Skip the search index file itself

        if os.path.isfile(file_path):
            process_file(file_path, txt_temp_path, writer)
            with open(marker_file_path, 'w') as marker_file:
                marker_file.write('')
            # Write to marker log file
            with open(marker_log_file_path, 'a') as marker_log_file:
                marker_log_file.write(file_name + '\n')

            # logging.info(f"Processed and marked: {file_name}")


def process_file(file_path, txt_temp_path, writer):
    file_name = os.path.basename(file_path)
    path_tail = get_path_tail(file_path)
    marker_file_path = os.path.join(txt_temp_path, file_name + '.processed')

    # DEBUG timer
    # time.sleep(2)

    # Check for the existence of a marker file
    # if os.path.exists(marker_file_path):
    if file_name in processed_files:
        print(f"Skipping already processed file: {file_name}")
        return

    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".pdf":
        logging.info(f"Processing PDF File: {file_name} in {path_tail}")
        convert_pdf_to_text(file_path, txt_temp_path, writer)
        # add_file_name_to_search_index(file_path, writer)
    elif file_extension in [".log", ".txt"]:
        logging.info(f"Processing Text/Log File: {file_name} in {path_tail}")
        process_text_file(file_path, txt_temp_path, writer)
        # add_file_name_to_search_index(file_path, writer)
    elif file_extension in [".mp4", ".dwg", ".tif", ".xls", ".xlsx", ".doc", ".docx"]:
        logging.info(f"Adding Filename: {file_name} in {path_tail}")
        add_file_name_to_search_index(file_path, writer)
    else:
        logging.info(f"Skipping File: {file_name}")

    processed_files.add(file_path)
    save_processed_file(file_path, txt_temp_path)


def save_processed_file(file_path, txt_temp_path):
    processed_file_path = os.path.join(txt_temp_path, os.path.basename(file_path))
    with open(processed_file_path, 'w') as f:
        f.write('')


def add_file_name_to_search_index(file_path, writer):
    file_name = os.path.basename(file_path)
    relative_path = get_relative_path(path_to_files, file_path)
    escaped_name = escape(file_name)

    writer.write("\t<file>\n")
    writer.write(f"\t\t<name>{escaped_name}</name>\n")
    writer.write(f"\t\t<path>{escape(relative_path)}</path>\n")
    writer.write("\t</file>\n")
    logging.info(f"Added filename to search index: {file_name}")


def get_relative_path(base_path, full_path):
    try:
        if not base_path.endswith(os.path.sep):
            base_path += os.path.sep
        base_uri = os.path.normpath(base_path)
        full_uri = os.path.normpath(full_path)
        return os.path.relpath(full_uri, base_uri)
    except ValueError as ex:
        logging.error(f"ValueError in get_relative_path: {ex}")
        return full_path


def process_text_file(file_path, txt_temp_path, writer):
    with open(file_path, 'r', encoding='utf-8') as text_file:
        text_content = text_file.read()
    temp_file_name = os.path.splitext(os.path.basename(file_path))[0] + ".txt"
    temp_file_path = os.path.join(txt_temp_path, temp_file_name)
    with open(temp_file_path, 'w', encoding='utf-8') as temp_file:
        temp_file.write(text_content)

    writer.write("\t<file>\n")
    writer.write(f"\t\t<name>{escape(os.path.basename(file_path))}</name>\n")
    writer.write(f"\t\t<path>{escape(get_relative_path(path_to_files, file_path))}</path>\n")
    writer.write("\t\t<page>\n")
    writer.write(f"{escape(text_content)}\n")
    writer.write("\t\t</page>\n")
    writer.write("\t</file>\n")

    # logging.info(f"Processed text/log file: {os.path.basename(file_path)}")


def convert_pdf_to_text(pdf_file_path, txt_temp_path, writer):
    text_file_name = os.path.splitext(os.path.basename(pdf_file_path))[0] + ".txt"
    text_file_path = os.path.join(txt_temp_path, text_file_name)

    if not os.path.exists(pdf_file_path):
        logging.error(f"PDF file does not exist: {pdf_file_path}")
        return
    if os.stat(pdf_file_path).st_size == 0:
        logging.error(f"PDF file is empty: {pdf_file_path}")
        return

    try:
        pdf_document = fitz.open(pdf_file_path)
        with open(text_file_path, 'w', encoding='utf-8') as text_file:
            writer.write("\t<file>\n")
            writer.write(f"\t\t<name>{escape(os.path.basename(pdf_file_path))}</name>\n")
            writer.write(f"\t\t<path>{escape(get_relative_path(path_to_files, pdf_file_path))}</path>\n")
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text = page.get_text()
                text_file.write(text)
                writer.write("\t\t<page>\n")
                writer.write(f"{escape(text)}\n")
                writer.write("\t\t</page>\n")
            writer.write("\t</file>\n")
        pdf_document.close()

    except Exception as e:
        logging.error(f"Exception in convert_pdf_to_text: {e}", exc_info=True)


def clean_up_temp_directory(txt_temp_path):
    if os.path.exists(txt_temp_path):
        shutil.rmtree(txt_temp_path)
        logging.info(f"Removed temporary directory: {txt_temp_path}")


if __name__ == "__main__":
    main(sys.argv)
