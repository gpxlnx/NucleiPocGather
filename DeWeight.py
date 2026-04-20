import os
import yaml
import hashlib
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor


def hash_content(content):
    """Calcula o hash do conteúdo informado."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def read_fields_from_yaml(file_path):
    """Lê campos relevantes do YAML e retorna o hash consolidado e o caminho do arquivo."""
    fields_to_read = ['requests', 'tcp', 'http', 'file', 'fingerprint', 'request', 'workflows', 'rules', 'network']
    found_fields = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

            for field in fields_to_read:
                value = data.get(field)
                if value is not None:
                    found_fields.append(str(value))

            if found_fields:
                combined_content = "\n".join(found_fields)
                return hash_content(combined_content), file_path

    except Exception:
        pass
    return None, None


def process_file(file_path):
    """Processa um arquivo YAML e retorna seu hash de conteúdo."""
    return read_fields_from_yaml(file_path)


def traverse_directory_and_read_fields(dir_path):
    """Percorre o diretório recursivamente e remove arquivos YAML semanticamente duplicados."""
    hash_dict = {}
    yaml_files = []

    for root, _, files in os.walk(dir_path):
        for filename in files:
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                yaml_files.append(os.path.join(root, filename))

    with ThreadPoolExecutor() as executor:
        results = list(tqdm(executor.map(process_file, yaml_files), total=len(yaml_files), desc="Progresso"))

    for file_hash, valid_file_path in results:
        if file_hash and valid_file_path:
            if file_hash in hash_dict:
                hash_dict[file_hash].append(valid_file_path)
            else:
                hash_dict[file_hash] = [valid_file_path]

    same_file_count = 0
    for file_hash, file_paths in hash_dict.items():
        if len(file_paths) > 1:
            shortest_file = min(file_paths, key=len)
            print(f"[+] Hash do arquivo: {file_hash} -> arquivos equivalentes: {', '.join(file_paths)}")
            print(f"[+] Arquivo mantido: [{shortest_file}]")

            for file_path in file_paths:
                if file_path != shortest_file:
                    os.remove(file_path)
                    print(f"[-] Arquivo removido: {file_path}")

            same_file_count += len(file_paths)

    print(f"\n[+] Total de arquivos equivalentes encontrados: {same_file_count}")


def deWeight():
    poc_directory = "poc"
    traverse_directory_and_read_fields(poc_directory)


if __name__ == "__main__":
    poc_directory = "poc"
    traverse_directory_and_read_fields(poc_directory)
