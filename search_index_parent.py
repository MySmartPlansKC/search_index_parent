# search_index_parent

import fitz  # PyMuPDF
import logging
import os
import re
import shutil
from xml.sax.saxutils import escape

# Versioning
__version__ = "1.2.0"
# pyinstaller --onefile --name search_index_parent-V1.2.0 search_index_parent.py

# Global variables
log_file_path = ""
marker_log_file_path = ""
path_to_files = ""

# Toggle for testing
USE_HARD_CODED_PATHS = True
# HARD_CODED_PATH_TO_FILES = r"E:\Python\xPDFTestFiles\searchIndexFiles"
HARD_CODED_PATH_TO_FILES = r"R:\_Nick\KCI Closeout\KCI Closeout\KCI Closeout\CD_Root\AutoPlay\Docs"


def main():
    try:
        initialize()
        processed_files = load_processed_files()
        accumulated_index_file_path = os.path.join(path_to_files, "search_index.xml")

        if not os.path.exists(accumulated_index_file_path) or os.stat(accumulated_index_file_path).st_size == 0:
            with open(accumulated_index_file_path, 'w', encoding='utf-8') as accumulated_writer:
                accumulated_writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
                accumulated_writer.write('<files>\n')
                traverse_main_folders(path_to_files, accumulated_writer, processed_files)
                accumulated_writer.write('</files>\n')

        else:
            with open(accumulated_index_file_path, 'a', encoding='utf-8') as accumulated_writer:
                traverse_main_folders(path_to_files, accumulated_writer, processed_files)

        logging.info("All directories processed successfully.")

    except OSError as e:
        logging.error(f"Script is already running: {e}")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)


def initialize():
    global path_to_files
    if USE_HARD_CODED_PATHS:
        path_to_files = HARD_CODED_PATH_TO_FILES
    else:
        path_to_files = os.getcwd()
    initialize_logging()
    logging.info(f"search_index_parent Version: {__version__}")


def initialize_logging():
    global marker_log_file_path

    marker_log_file_path = os.path.join(path_to_files, "processed_files_log.txt")

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[console_handler]
    )


def setup_error_logging():
    global log_file_path
    if not log_file_path:
        log_file_path = os.path.join(path_to_files, "search_builder_error_log.txt")

    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.ERROR)

    logging.getLogger().addHandler(file_handler)


def get_path_tail(path):
    parts = path.split(os.sep)

    if os.path.isfile(path):
        parts = parts[:-1]

    if len(parts) >= 2:
        return os.path.join(parts[-2], parts[-1])
    elif len(parts) == 1:
        return parts[0]
    return ""


def load_processed_files():
    processed_files = set()
    if os.path.exists(marker_log_file_path):
        with open(marker_log_file_path, 'r') as f:
            processed_files = {os.path.normpath(line.strip()) for line in f}
    return processed_files


def traverse_main_folders(root_path, accumulated_writer, processed_files):
    skip_folders = {}
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if item in skip_folders:
            logging.info(f"Skipping directory due to filter: {item}")
            continue
        if os.path.isdir(item_path):
            logging.info(f"Processing directory: {item_path}")
            if item.lower() == "no classification":
                # Process NO CLASSIFICATION folder as root
                process_no_classification_folder(item_path, accumulated_writer, processed_files)
            else:
                process_main_folder(item_path, accumulated_writer, processed_files)


def process_main_folder(directory_path, accumulated_writer, processed_files):
    index_file_path = os.path.join(directory_path, "search_index.xml")
    needs_header = not os.path.exists(index_file_path) or os.stat(index_file_path).st_size == 0

    with open(index_file_path, 'a', encoding='utf-8') as writer:
        if needs_header:
            writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
            writer.write('<files>\n')

        traverse_and_process_directory(directory_path, writer, processed_files)

        if needs_header:
            writer.write('</files>\n')

    logging.info(f"Created/Updated search index for {os.path.basename(directory_path)}")
    if needs_header:
        append_to_accumulated_index(index_file_path, accumulated_writer)


def process_no_classification_folder(directory_path, accumulated_writer, processed_files):
    skip_folders = {}
    no_class_accumulated_path = os.path.join(directory_path, "search_index.xml")
    needs_header = not os.path.exists(no_class_accumulated_path) or os.stat(no_class_accumulated_path).st_size == 0

    with open(no_class_accumulated_path, 'a', encoding='utf-8') as no_class_accumulated_writer:
        if needs_header:
            no_class_accumulated_writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
            no_class_accumulated_writer.write('<files>\n')

        for sub_directory in os.listdir(directory_path):
            sub_directory_path = os.path.join(directory_path, sub_directory)
            if os.path.isdir(sub_directory_path) and sub_directory not in skip_folders:
                process_sub_folder(sub_directory_path, no_class_accumulated_writer,
                                   processed_files, include_subdirectories=True)

        if needs_header:
            no_class_accumulated_writer.write('</files>\n')

        logging.info(f"Created/Updated search index for {os.path.basename(directory_path)} (NO CLASSIFICATION)")
        append_to_accumulated_index(no_class_accumulated_path, accumulated_writer)


def process_sub_folder(directory_path, accumulated_writer, processed_files, include_subdirectories=False):
    sub_index_file_path = os.path.join(directory_path, "search_index.xml")
    needs_header = not os.path.exists(sub_index_file_path) or os.stat(sub_index_file_path).st_size == 0

    with open(sub_index_file_path, 'a', encoding='utf-8') as sub_writer:
        if needs_header:
            sub_writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
            sub_writer.write('<files>\n')

        traverse_and_process_directory(directory_path, sub_writer, processed_files, include_subdirectories)

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


def traverse_and_process_directory(directory_path, writer, processed_files, include_subdirectories=False):
    process_files_in_directory(directory_path, writer, processed_files)
    for sub_directory in os.listdir(directory_path):
        sub_directory_path = os.path.join(directory_path, sub_directory)
        if os.path.isdir(sub_directory_path):
            if include_subdirectories:
                process_sub_folder(sub_directory_path, writer, processed_files, include_subdirectories=True)
            else:
                traverse_and_process_directory(sub_directory_path, writer, processed_files)


def process_files_in_directory(directory_path, writer, processed_files):
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        relative_file_path = os.path.relpath(file_path, path_to_files)

        if file_name.lower() == "search_index.xml" or relative_file_path in processed_files:
            logging.info(f"Skipping File: {relative_file_path}")
            continue  # Skip the search index file itself

        if os.path.isfile(file_path):
            if relative_file_path not in processed_files:
                process_file(file_path, writer, relative_file_path, processed_files)

                # logging.info(f"Processed file: {relative_file_path}")
                with open(marker_log_file_path, 'a', encoding='utf-8') as marker_log_file:
                    marker_log_file.write(relative_file_path + '\n')
                    processed_files.add(relative_file_path)


def process_file(file_path, writer, relative_file_path, processed_files):
    file_name = os.path.basename(file_path)
    path_tail = get_path_tail(file_path)

    if relative_file_path in processed_files:
        print(f"Skipping already processed file: {file_name}")
        return

    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".pdf":
        logging.info(f"Processing PDF File: {file_name} in {path_tail}")
        convert_pdf_to_text(file_path, writer)
    elif file_extension in [".log", ".txt"]:
        logging.info(f"Processing Text/Log File: {file_name} in {path_tail}")
        process_text_file(file_path, writer)
    else:
        logging.info(f"Adding Filename: {file_name} in {path_tail}")
        add_file_name_to_search_index(file_path, writer)

    processed_files.add(file_path)


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


def process_text_file(file_path, writer):
    try:
        with open(file_path, 'r', encoding='utf-8') as text_file:
            text_content = text_file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='windows-1252') as text_file:
                text_content = text_file.read()
        except UnicodeDecodeError:
            logging.error(f"Could not read file {file_path} with either UTF-8 or Windows-1252 encoding. Skipping file.")
            return

    file_name = os.path.basename(file_path)
    escaped_name = escape(file_name)
    escaped_text_content = escape(text_content)

    writer.write("\t<file>\n")
    writer.write(f"\t\t<name>{escaped_name}</name>\n")
    writer.write("\t\t<page>\n")
    writer.write(f"{escaped_text_content}\n")
    writer.write("\t\t</page>\n")
    writer.write("\t</file>\n")


def convert_pdf_to_text(pdf_file_path, writer):
    if not os.path.exists(pdf_file_path):
        logging.error(f"PDF file does not exist: {pdf_file_path}")
        return
    if os.stat(pdf_file_path).st_size == 0:
        logging.error(f"PDF file is empty: {pdf_file_path}")
        return

    try:
        pdf_document = fitz.open(pdf_file_path)
        file_name = os.path.basename(pdf_file_path)
        escaped_name = escape(file_name)

        writer.write("\t<file>\n")
        writer.write(f"\t\t<name>{escaped_name}</name>\n")

        for page in pdf_document:
            text = page.get_text()
            cleaned_text = re.sub(r'[^\x20-\x7E]+', '', text)
            sanitized_text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]", "", cleaned_text)
            trimmed_text = sanitized_text.strip()  # Trim leading and trailing whitespace

            writer.write(f"\t\t<page>{escape(trimmed_text)}</page>\n")

        writer.write("\t</file>\n")
        pdf_document.close()

    except Exception as e:
        logging.error(f"Exception in convert_pdf_to_text: {e}", exc_info=True)


def clean_up_temp_directory(txt_temp_path):
    if os.path.exists(txt_temp_path):
        shutil.rmtree(txt_temp_path)
        logging.info(f"Removed temporary directory: {txt_temp_path}")


if __name__ == "__main__":
    main()
