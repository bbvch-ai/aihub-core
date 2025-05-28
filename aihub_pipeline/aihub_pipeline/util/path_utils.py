import os


def get_document_figures_folder_name(uri: str, figures_directory_name: str) -> str:
    base_path = os.path.dirname(uri)
    doc_name, doc_type = os.path.basename(uri).split(".")
    doc_name = f"{doc_name}_{doc_type}"
    return f"{base_path}/{figures_directory_name}/{doc_name}"


def get_data_lake_client_figure_path(figure_path: str) -> str:
    figure_path = "/".join(figure_path.split("/")[1:])
    return figure_path
