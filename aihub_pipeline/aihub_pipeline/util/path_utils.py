import os


def get_container_name(uri: str):
    base_path = os.path.dirname(uri)
    return base_path.split("/")[0]


def get_document_figures_folder_name(uri: str):
    base_path = os.path.dirname(uri)
    doc_name, doc_type = os.path.basename(uri).split(".")
    doc_name = f"{doc_name}_{doc_type}"
    base_dir = base_path.split("/")[1]
    return f"{base_dir}/figures/{doc_name}"
