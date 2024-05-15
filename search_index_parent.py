# search_index_parent

import fitz  # PyMuPDF
import logging
import os
import shutil
import sys
from xml.sax.saxutils import escape

# Versioning
__version__ = "1.1.0"
# pyinstaller --onefile --name search_index_parent-V1.1.0 search_index_parent.py

# Global variables
log_file_path = ""
path_to_files = ""
processed_files = set()
file_count = 0
current_file_index = 0

# Toggle for testing
USE_HARD_CODED_PATHS = False
HARD_CODED_PATH_TO_FILES = r"E:\Testing Directory\Docs"


def main(args):
    initialize(args)
    txt_temp_path = create_temp_directory(path_to_files)

    # Create the main search index file in the root directory
    accumulated_index_file_path = os.path.join(path_to_files, "search_index.xml")
    with open(accumulated_index_file_path, 'w', encoding='utf-8') as accumulated_writer:
        accumulated_writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
        accumulated_writer.write('<files>\n')

        # Process the root directory
        process_files_in_directory(path_to_files, txt_temp_path, accumulated_writer)

        # Traverse and process subdirectories
        traverse_main_folders(path_to_files, txt_temp_path, accumulated_writer)

        accumulated_writer.write('</files>\n')

    clean_up_temp_directory(txt_temp_path)
    logging.info("All directories processed successfully.")


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
    global log_file_path
    log_file_path = os.path.join(path_to_files, "search_builder_processing_log.txt")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )


def create_temp_directory(directory_path):
    txt_temp_path = os.path.join(directory_path, "txtTemp")
    os.makedirs(txt_temp_path, exist_ok=True)
    return txt_temp_path


def traverse_main_folders(root_path, txt_temp_path, accumulated_writer):
    for item in os.listdir(root_path):
        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            if item.lower() == "no classification":
                # Process NO CLASSIFICATION folder as root
                process_no_classification_folder(item_path, txt_temp_path, accumulated_writer)
            else:
                processed_files.clear()  # Clear processed files for each main directory
                index_file_path = os.path.join(item_path, "search_index.xml")
                with open(index_file_path, 'w', encoding='utf-8') as writer:
                    writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
                    writer.write('<files>\n')
                    traverse_and_process_directory(item_path, txt_temp_path, writer)
                    writer.write('</files>\n')
                logging.info(f"Created/Updated search index for {os.path.basename(item_path)}")

                # Add the contents of this search index to the accumulated search index
                with open(index_file_path, 'r', encoding='utf-8') as reader:
                    for line in reader:
                        if line.strip() != '<?xml version="1.0" encoding="utf-8"?>' and line.strip() != '<files>' and line.strip() != '</files>':
                            accumulated_writer.write(line)
        # elif os.path.isfile(item_path) and item.lower() == "search_index.xml":
        #     logging.info(f"Skipping File: {item}")


def process_no_classification_folder(directory_path, txt_temp_path, accumulated_writer):
    processed_files.clear()  # Clear processed files for the NO CLASSIFICATION directory
    index_file_path = os.path.join(directory_path, "search_index.xml")
    with open(index_file_path, 'w', encoding='utf-8') as writer:
        writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
        writer.write('<files>\n')
        traverse_and_process_directory(directory_path, txt_temp_path, writer, include_subdirectories=True)
        writer.write('</files>\n')
    logging.info(f"Created/Updated search index for {os.path.basename(directory_path)} (NO CLASSIFICATION)")

    # Add the contents of this search index to the accumulated search index
    with open(index_file_path, 'r', encoding='utf-8') as reader:
        for line in reader:
            if line.strip() != '<?xml version="1.0" encoding="utf-8"?>' and line.strip() != '<files>' and line.strip() != '</files>':
                accumulated_writer.write(line)


def traverse_and_process_directory(directory_path, txt_temp_path, writer, include_subdirectories=False):
    process_files_in_directory(directory_path, txt_temp_path, writer)
    if include_subdirectories:
        for sub_directory in os.listdir(directory_path):
            sub_directory_path = os.path.join(directory_path, sub_directory)
            if os.path.isdir(sub_directory_path):
                index_file_path = os.path.join(sub_directory_path, "search_index.xml")
                with open(index_file_path, 'w', encoding='utf-8') as sub_writer:
                    sub_writer.write('<?xml version="1.0" encoding="utf-8"?>\n')
                    sub_writer.write('<files>\n')
                    traverse_and_process_directory(sub_directory_path, txt_temp_path, sub_writer, include_subdirectories)
                    sub_writer.write('</files>\n')
                logging.info(f"Created/Updated search index for {os.path.basename(sub_directory_path)}")


def process_files_in_directory(directory_path, txt_temp_path, writer):
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        if file_name.lower() == "search_index.xml":
            # logging.info(f"Skipping File: {file_name}")
            continue  # Skip the search index file itself

        if os.path.isfile(file_path):
            if file_path not in processed_files:
                process_file(file_path, txt_temp_path, writer)
                processed_files.add(file_path)


def process_file(file_path, txt_temp_path, writer):
    if file_path in processed_files:
        return

    file_extension = os.path.splitext(file_path)[1].lower()
    processing_functions = {
        '.pdf': process_pdf_file,
        '.log': process_text_file,
        '.txt': process_text_file,
        '.mp4': add_file_name_to_search_index,
        '.dwg': add_file_name_to_search_index,
        '.tif': add_file_name_to_search_index,
        '.xls': add_file_name_to_search_index,
        '.xlsx': add_file_name_to_search_index,
        '.doc': add_file_name_to_search_index,
        '.docx': add_file_name_to_search_index,
        # Add more mappings as needed
    }

    # func = processing_functions.get(file_extension, default_file_processing)
    func = processing_functions.get(file_extension)
    func(file_path, txt_temp_path, writer)
    processed_files.add(file_path)


# def default_file_processing(file_path, txt_temp_path, writer):
#     logging.info(f"Skipping File: {os.path.basename(file_path)}")


def add_file_name_to_search_index(file_path, txt_temp_path, writer):
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
    try:
        with open(file_path, 'r', encoding='utf-8') as text_file:
            writer.write("\t<file>\n")
            writer.write(f"\t\t<name>{escape(os.path.basename(file_path))}</name>\n")
            writer.write(f"\t\t<path>{escape(get_relative_path(path_to_files, file_path))}</path>\n")
            writer.write("\t\t<content>\n")
            for line in text_file:
                writer.write(f"{escape(line)}")
            writer.write("\t\t</content>\n")
            writer.write("\t</file>\n")
    except Exception as e:
        logging.error(f"Exception in process_text_file: {e}")


def process_pdf_file(pdf_file_path, txt_temp_path, writer):
    try:
        with fitz.open(pdf_file_path) as pdf_document:
            writer.write("\t<file>\n")
            writer.write(f"\t\t<name>{escape(os.path.basename(pdf_file_path))}</name>\n")
            writer.write(f"\t\t<path>{escape(get_relative_path(path_to_files, pdf_file_path))}</path>\n")
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text = page.get_text()
                writer.write("\t\t<page>\n")
                writer.write(f"{escape(text)}\n")
                writer.write("\t\t</page>\n")
            writer.write("\t</file>\n")
    except Exception as e:
        logging.error(f"Exception in convert_pdf_to_text: {e}")

    logging.info(f"Processed PDF: {os.path.basename(pdf_file_path)}")


def clean_up_temp_directory(txt_temp_path):
    if os.path.exists(txt_temp_path):
        shutil.rmtree(txt_temp_path)
        logging.info(f"Removed temporary directory: {txt_temp_path}")


if __name__ == "__main__":
    main(sys.argv)