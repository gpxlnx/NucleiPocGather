import os
import yaml
import concurrent.futures
from collections import defaultdict, Counter
from datetime import datetime
from tqdm import tqdm


STATS_START_MARKER = "<!-- stats:start -->\n"
STATS_END_MARKER = "<!-- stats:end -->\n"


def process_yaml_file(file_path):
    """Processa um arquivo YAML e retorna as tags e a severidade encontradas."""
    tags = []
    severity = None
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
            if 'info' in data:
                tags = [tag.strip() for tag in data['info'].get('tags', '').split(',')] if 'tags' in data['info'] else []
                severity = data['info'].get('severity', None)
                if severity:
                    severity = severity.lower()
    except Exception:
        pass
    return tags, severity


def count_tags_and_severity_in_yaml_files(directory):
    """Conta recursivamente as tags e severidades dos arquivos YAML."""
    all_tags = []
    severities = []

    yaml_files = [os.path.join(root, filename) for root, _, files in os.walk(directory)
                  for filename in files if filename.endswith(('.yaml', '.yml'))]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for tags, severity in tqdm(executor.map(process_yaml_file, yaml_files), total=len(yaml_files), desc="Processando arquivos YAML"):
            all_tags.extend(tags)
            if severity:
                severities.append(severity)

    return all_tags, severities


def get_top_n_items(items_list, n=10):
    """Retorna os N itens mais frequentes."""
    counter = Counter(items_list)
    return counter.most_common(n)


def get_current_time():
    """Retorna a data e hora atual no formato do README."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M")


def count_yaml_files_in_subdirectories(directory):
    """Conta arquivos YAML por subdiretório e retorna os 10 maiores."""
    yaml_counts = defaultdict(int)

    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            yaml_counts[item] = sum(1 for subitem in os.listdir(item_path) if subitem.endswith(('.yaml', '.yml')))

    return sorted(yaml_counts.items(), key=lambda x: x[1], reverse=True)[:10]


def build_stats_block(poc_directory_count, yaml_file_count, new_table_data):
    """Monta o bloco de estatísticas do README entre os marcadores dedicados."""
    current_time = get_current_time()
    lines = [
        STATS_START_MARKER,
        f"> **Atualização dos POCs do projeto:** `{current_time}`\n",
        "\n",
        "| ID | Tag | Quantidade | Diretório | Quantidade | Severidade | Quantidade |\n",
        "|:---|:----|-----------:|:----------|-----------:|:-----------|-----------:|\n",
    ]

    for index, label, count, directory, dir_count, severity, sev_count in new_table_data:
        lines.append(
            f"| {index} | {label} | {count} | {directory} | {dir_count} | {severity} | {sev_count} |\n"
        )

    lines.extend([
        "\n",
        f"**{poc_directory_count} diretórios, {yaml_file_count} arquivos**\n",
        STATS_END_MARKER,
    ])
    return lines


def update_readme(poc_directory_count, yaml_file_count, new_table_data):
    """Atualiza apenas a seção de estatísticas do README.md."""
    with open('README.md', 'r', encoding='utf-8') as file:
        content = file.readlines()

    try:
        start_index = content.index(STATS_START_MARKER)
        end_index = content.index(STATS_END_MARKER)
    except ValueError as exc:
        raise RuntimeError("Os marcadores de estatística não foram encontrados em README.md") from exc

    new_block = build_stats_block(poc_directory_count, yaml_file_count, new_table_data)
    updated_content = content[:start_index] + new_block + content[end_index + 1:]

    with open('README.md', 'w', encoding='utf-8') as file:
        file.writelines(updated_content)


def wirte_readme():
    poc_directory = "poc"

    yaml_file_count = sum(1 for root, _, files in os.walk(poc_directory)
                          for filename in files if filename.endswith(('.yaml', '.yml')))
    print(f"Foram encontrados {yaml_file_count} arquivos YAML no diretório '{poc_directory}'.")

    top_yaml_counts = count_yaml_files_in_subdirectories(poc_directory)
    print("\nTop 10 diretórios com mais arquivos YAML:")
    for subdir, count in top_yaml_counts:
        print(f"{subdir}: {count} arquivos YAML")

    all_tags, severities = count_tags_and_severity_in_yaml_files(poc_directory)

    top_tags = get_top_n_items(all_tags, n=10)
    top_severities = get_top_n_items(severities, n=10)

    print("\nTop 10 tags por ocorrência:")
    for tag, count in top_tags:
        print(f"{tag}: {count} ocorrências")

    print("\nTop 10 severidades por ocorrência:")
    for severity, count in top_severities:
        print(f"{severity}: {count} ocorrências")

    new_table_data = []
    for i in range(10):
        tag_label, tag_count = top_tags[i] if i < len(top_tags) else ("-", 0)
        dir_label, dir_count = top_yaml_counts[i] if i < len(top_yaml_counts) else ("-", 0)
        severity_label, severity_count = top_severities[i] if i < len(top_severities) else ("-", 0)
        new_table_data.append((i + 1, tag_label, int(tag_count), dir_label, int(dir_count), severity_label, int(severity_count)))

    update_readme(len(top_yaml_counts), yaml_file_count, new_table_data)


if __name__ == "__main__":
    wirte_readme()
