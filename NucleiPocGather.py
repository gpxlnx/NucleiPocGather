import os
import shutil
import hashlib
import requests
from collections import defaultdict
from tqdm import tqdm
import concurrent.futures
import WirteREADME
from DeWeight import deWeight


class RepoManager:
    def __init__(self, repo_file, clone_dir):
        self.repo_file = repo_file  # Caminho do arquivo com as URLs dos repositórios.
        self.clone_dir = clone_dir  # Diretório de destino dos clones.

    def ensure_clone_directory(self):
        try:
            os.makedirs(self.clone_dir, exist_ok=True)
        except OSError as e:
            print(f"[x] Erro ao criar o diretório {self.clone_dir}: {e}")
            return False
        return True

    def read_repo_file(self):
        try:
            with open(self.repo_file, 'r') as file:
                urls = list(set(line.strip() for line in file if line.strip()))
            return urls
        except FileNotFoundError:
            print(f"[x] Arquivo {self.repo_file} não encontrado.")
        except Exception as e:
            print(f"[x] Erro ao ler o arquivo {self.repo_file}: {e}")
        return []

    def process_repos(self, urls):
        for url in urls:
            parts = url.split('/')
            if len(parts) >= 2:
                owner, repo_name = parts[-2], parts[-1]
                target_dir = os.path.join(self.clone_dir, f"{owner}/{repo_name}".lower())
            else:
                print(f"[x] Formato de URL inválido: {url}")
                continue

            if os.path.isdir(target_dir):
                self.update_repo(repo_name, target_dir)
            else:
                self.clone_repo(url, repo_name, target_dir)

    def update_repo(self, repo_name, target_dir):
        print(f"[+] Atualizando {repo_name} em {target_dir}")
        try:
            result = os.system(f"git -C {target_dir} pull")
            if result != 0:
                print(f"[x] Erro ao atualizar o repositório {repo_name} em {target_dir}")
        except Exception as e:
            print(f"[x] Erro ao atualizar o repositório {repo_name} em {target_dir}: {e}")

    def clone_repo(self, url, repo_name, target_dir):
        print(f"[+] Clonando {repo_name} para {target_dir}")
        try:
            result = os.system(f"git clone {url} {target_dir}")
            if result != 0:
                print(f"[x] Erro ao clonar o repositório {repo_name} para {target_dir}")
        except Exception as e:
            print(f"[x] Erro ao clonar o repositório {repo_name} para {target_dir}: {e}")

    def run(self):
        if not self.ensure_clone_directory():
            return
        urls = self.read_repo_file()
        self.process_repos(urls)


class NucleiDownloader:
    def __init__(self, repo_owner, repo_name):
        self.repo_owner = repo_owner  # Dono do repositório.
        self.repo_name = repo_name  # Nome do repositório.

    def get_latest_release(self):
        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        raise Exception("[x] Falha ao obter a versão mais recente")

    def download_file(self, url, dest):
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(dest, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
        else:
            raise Exception(f"[x] Falha ao baixar o arquivo: {url}")

    def find_download_url(self, assets, platform='linux', architecture='amd64', file_extension='.zip'):
        for asset in assets:
            if platform in asset['name'] and architecture in asset['name'] and asset['name'].endswith(file_extension):
                return asset['browser_download_url']
        return None

    def download_latest_release(self, dest_file):
        release = self.get_latest_release()
        assets = release['assets']

        download_url = self.find_download_url(assets)
        if not download_url:
            raise Exception("[x] Nenhum arquivo ZIP compatível com Linux amd64 foi encontrado")

        print(f"[+] Baixando de {download_url}")
        self.download_file(download_url, dest_file)
        print("[+] Arquivo ZIP do Nuclei baixado com sucesso")


class POCValidator:
    def __init__(self, poc_dir, nuclei_executable="./nuclei"):
        self.poc_dir = poc_dir  # Diretório dos arquivos POC.
        self.nuclei_executable = nuclei_executable  # Caminho do binário do Nuclei.

    def get_yaml_files(self):
        return [f for f in os.listdir(self.poc_dir) if f.endswith('.yaml') or f.endswith('.yml')]

    def validate_poc(self, file_path):
        command = f"{self.nuclei_executable} -t {file_path} -silent"
        return_code = os.system(command)
        return return_code == 0

    def process_files(self):
        yaml_files = self.get_yaml_files()
        for file in yaml_files:
            file_path = os.path.join(self.poc_dir, file)
            print(f"[+] Validando o POC {file_path}...")

            if self.validate_poc(file_path):
                print(f"[+] {file_path} possui formato válido")
            else:
                print(f"[x] {file_path} possui formato inválido e será removido")
                os.remove(file_path)


class POCOrganizer:
    def __init__(self, community_path, source_of_truth, output_path, category_map):
        self.community_path = community_path  # Caminho dos templates coletados da comunidade.
        self.source_of_truth = source_of_truth  # Caminho dos templates oficiais do projeto.
        self.output_path = output_path  # Diretório de saída.
        self.category_map = category_map  # Mapeamento de categorias.
        self.category_counts = {}  # Contagem de arquivos por categoria.
        self.file_hashes = {}  # Hashes por categoria para evitar cópias repetidas.

    def get_all_yaml_files(self, dir_path):
        all_yaml_files = {}
        for dirpath, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d != ".git" and d != "projectdiscovery__nuclei-templates"]
            for filename in files:
                if filename.endswith(".yml") or filename.endswith(".yaml"):
                    all_yaml_files[filename] = os.path.join(dirpath, filename)
        return all_yaml_files

    def categorize_file(self, file_name):
        categories = []
        for category, keywords in self.category_map.items():
            if any(keyword in file_name.lower() for keyword in keywords):
                categories.append(category)
        return categories if categories else ["other"]

    def file_hash(self, file_path):
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def copy_file_to_categories(self, file_path, categories, file_hash_value):
        for category in categories:
            target_dir = os.path.join(self.output_path, category)
            os.makedirs(target_dir, exist_ok=True)

            if file_hash_value not in self.file_hashes.get(category, set()):
                shutil.copy(file_path, os.path.join(target_dir, os.path.basename(file_path)))
                self.category_counts[category] = self.category_counts.get(category, 0) + 1
                self.file_hashes.setdefault(category, set()).add(file_hash_value)

    def get_file_size(self, file_path):
        return os.path.getsize(file_path)

    def process_files(self):
        community = self.get_all_yaml_files(self.community_path)
        nuclei_templates = self.get_all_yaml_files(self.source_of_truth)

        common_templates = set(community.keys()) & set(nuclei_templates.keys())

        for template, community_file in community.items():
            if template in common_templates and self.get_file_size(community_file) == self.get_file_size(
                    nuclei_templates[template]):
                os.remove(community_file)
                continue

            categories = self.categorize_file(os.path.basename(community_file))
            file_hash_value = self.file_hash(community_file)
            self.copy_file_to_categories(community_file, categories, file_hash_value)

    def print_summary(self):
        print("[+] Quantidade de arquivos por categoria:")
        total_count = 0
        for category, count in self.category_counts.items():
            total_count += count
            print(f"[+] {category}: {count}")
        print(f"[+] total: {total_count}")


class DuplicateFileHandler:
    def __init__(self, base_dir):
        self.base_dir = base_dir  # Diretório base.
        self.file_hashes = defaultdict(list)  # Hashes de arquivos.
        self.duplicate_files = {}  # Arquivos duplicados.

    @staticmethod
    def calculate_file_hash(file_path):
        """Calcula o hash MD5 de um arquivo."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def get_yaml_files(self):
        """Percorre o diretório recursivamente e retorna todos os arquivos YAML."""
        file_paths = []
        for root, _, files in os.walk(self.base_dir):
            for filename in files:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    file_path = os.path.join(root, filename)
                    file_paths.append(file_path)
        return file_paths

    def find_duplicate_files(self, file_paths):
        """Encontra arquivos com conteúdo idêntico."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.calculate_file_hash, file_path): file_path for file_path in file_paths}
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(file_paths), desc="Calculando hashes dos arquivos"):
                file_path = futures[future]
                file_hash = future.result()
                self.file_hashes[file_hash].append(file_path)

        self.duplicate_files = {hash_value: files for hash_value, files in self.file_hashes.items() if len(files) > 1}

    def print_and_remove_duplicate_files(self):
        """Exibe e remove arquivos duplicados, mantendo apenas uma cópia."""
        total_duplicates = 0

        for hash_value, files in self.duplicate_files.items():
            print(f"[+] Os arquivos com hash {hash_value} possuem o mesmo conteúdo:")
            for file in files:
                print(f"  {file}")

            for file_to_remove in files[1:]:
                os.remove(file_to_remove)
                print(f"[+] Arquivo removido: {file_to_remove}")
                total_duplicates += 1

        print(f"[+] Total de grupos de arquivos duplicados: {len(self.duplicate_files)}")
        print(f"[+] Total de arquivos duplicados removidos: {total_duplicates}")

    def process(self):
        file_paths = self.get_yaml_files()
        print(f"[+] {len(file_paths)} arquivos YAML encontrados.")

        self.find_duplicate_files(file_paths)
        self.print_and_remove_duplicate_files()


def pocfenlei():
    category_map = {
        "wordpress": ["wp", "wordpress"],
        "xss": ["xss"],
        "sql_injection": ["sqli", "sql_injection", "sql"],
        "local_file_inclusion": ["lfi", "local_file_inclusion"],
        "remote_code_execution": ["rce"],
        "cross_site_request_forgery": ["csrf"],
        "xml_external_entity": ["xxe"],
        "cve": ["cve"],
        "cnvd": ["cnvd"],
        "cnnvd": ["cnnvd"],
        "open_redirect": ["redirect", "open_redirect"],
        "ssrf": ["ssrf", "server_side_request_forgery"],
        "subdomain_takeover": ["subdomain_takeover", "takeover"],
        "template_injection": ["template_injection", "ssti"],
        "crlf_injection": ["crlf_injection", "crlf"],
        "directory_listing": ["directory_listing", "traversal"],
        "exposed": ["exposed", "disclosure", "sensitive", "exposure"],
        "adobe": ["adobe", "aem"],
        "coldfusion": ["coldfusion", "cfm"],
        "drupal": ["drupal"],
        "joomla": ["joomla"],
        "magento": ["magento"],
        "php": ["php"],
        "airflow": ["airflow"],
        "aws": ["aws", "amazon", "ec2", "s3", "lambda", "cloudfront", "cloudfront"],
        "apache": ["apache"],
        "cpanel": ["cpanel"],
        "docker": ["docker", "container", "kubernetes"],
        "git": ["git"],
        "jenkins": ["jenkins"],
        "cisco": ["cisco"],
        "api": ["api"],
        "upload": ["upload"],
        "sensitive": ["sensitive"],
        "debug": ["debug"],
        "backup": ["backup"],
        "auth": [
            "auth", "login", "signin", "sign_in", "sign-in", "oauth", "sso", "register", "signup",
            "sign_up", "sign-up", "password", "pwd", "passwd", "secret", "token", "credential", "cred",
            "jwt", "cookie", "session", "remember", "keycloak", "key"
        ],
        "atlassian": ["atlassian", "jira", "confluence", "bitbucket", "bamboo"],
        "config": ["config", "conf", "configuration"],
        "mysql": ["mysql", "mariadb"],
        "sql": ["sql", "database", "db"],
        "default": ["default"],
        "detect": ["detect"],
        "extract": ["extract"],
        "fuzz": ["fuzz"],
        "graphql": ["graphql"],
        "http": ["http"],
        "social": ["social", "social_media", "facebook", "twitter", "instagram", "linkedin"],
        "favicon": ["favicon"],
        "python": ["python", "flask", "django"],
        "ftp": ["ftp"],
        "gcloud": ["gcloud", "google_cloud", "gcp"],
        "google": ["google"],
        "graphite": ["graphite"],
        "header": ["header"],
        "injection": ["injection"],
        "ibm": ["ibm"],
        "search": ["search"],
        "ldap": ["ldap"],
        "microsoft": ["microsoft", "ms"],
        "mongodb": ["mongodb", "mongo"],
        "netlify": ["netlify"],
        "oracle": ["oracle"],
        "java": [
            "java", "jsp", "jsf", "j2ee", "j2se", "j2me", "jvm", "jre", "jdk", "jboss", "tomcat",
            "glassfish", "wildfly", "jetty", "websphere", "weblogic", "spring", "struts", "hibernate",
            "mybatis", "shiro"
        ],
        "javascript": ["javascript", "js"],
        "elk": ["elk", "elasticsearch", "kibana", "logstash"],
        "kafka": ["kafka"],
        "kong": ["kong"],
        "laravel": ["laravel"],
        "nginx": ["nginx"],
        "nodejs": ["nodejs", "node", "express", "npm"],
        "perl": ["perl"],
        "postgres": ["postgres", "postgresql"],
        "rabbitmq": ["rabbitmq"],
        "redis": ["redis"],
        "ruby": ["ruby", "rails"],
        "samba": ["samba"],
        "sharepoint": ["sharepoint"],
        "smtp": ["smtp"],
        "sap": ["sap"],
        "shopify": ["shopify"],
        "ssh": ["ssh"],
        "vmware": ["vmware"],
        "web": ["web"],
    }

    community_path = "clone-templates"
    source_of_truth = "clone-templates/projectdiscovery/nuclei-templates"
    output_path = "poc"

    organizer = POCOrganizer(community_path, source_of_truth, output_path, category_map)
    organizer.process_files()
    organizer.print_summary()

    os.system('rm -rf clone-templates')


def getPocName():
    os.system('find . -type f \\( -iname "*.yaml" -o -iname "*.yml" \\)| sort > poc.txt')
    print("[+] Todos os nomes de POCs foram gravados no arquivo poc.txt")


def run():
    # 1. Lê a lista de repositórios e faz clone ou atualização.
    repo_file = "repo.txt"
    clone_dir = "clone-templates"
    manager = RepoManager(repo_file, clone_dir)
    manager.run()

    # 2. Baixa o binário do Nuclei para validar templates.
    downloader = NucleiDownloader(repo_owner="projectdiscovery", repo_name="nuclei")
    downloader.download_latest_release(dest_file="nuclei.zip")
    os.system("unzip nuclei.zip nuclei")
    os.system("rm -rf nuclei.zip")

    # 3. Valida os POCs clonados e remove os inválidos.
    poc_validator = POCValidator(poc_dir="clone-templates")
    poc_validator.process_files()

    # 4. Classifica todos os POCs válidos em diretórios por categoria.
    pocfenlei()

    # 5. Remove arquivos com conteúdo idêntico do diretório final.
    base_dir = os.path.join(os.getcwd(), 'poc')
    handler = DuplicateFileHandler(base_dir)
    handler.process()

    # 6. Gera um inventário com os nomes de todos os POCs.
    getPocName()

    # 7. Executa uma deduplicação adicional baseada no conteúdo dos campos principais.
    deWeight()

    # 8. Atualiza as estatísticas do README.
    WirteREADME.wirte_readme()


if __name__ == '__main__':
    run()
