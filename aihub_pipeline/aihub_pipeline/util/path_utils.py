import os


def create_data_lake_figures_folder_name(uri: str, figures_directory_name: str) -> str:
    base_path = os.path.dirname(uri)
    file_name = os.path.basename(uri)
    doc_name, doc_type = os.path.splitext(file_name)
    doc_name = f"{doc_name}_{doc_type[1:]}"
    return f"{base_path}/{figures_directory_name}/{doc_name}"
