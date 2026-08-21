# NucleiPocGather

Coletor e organizador de templates Nuclei com atualização automatizada.

Este projeto usa Python para buscar templates Nuclei de vários repositórios GitHub, validar os arquivos encontrados, remover duplicidades, classificar os POCs em categorias e atualizar este `README.md` com estatísticas da coleção.

## O que o script faz

O fluxo principal do arquivo `NucleiPocGather.py` executa estas etapas:

1. Lê o arquivo `repo.txt` com a lista de repositórios-fonte.
2. Faz `git clone` ou `git pull` desses repositórios em `clone-templates/`.
3. Baixa a versão mais recente do binário `nuclei` para Linux `amd64`.
4. Valida os templates YAML clonados e remove os inválidos.
5. Compara os templates comunitários com os oficiais do `projectdiscovery/nuclei-templates`.
6. Descarta arquivos iguais aos templates oficiais e classifica o restante em `poc/<categoria>/`.
7. Remove duplicados por hash de arquivo e por conteúdo semântico dos campos principais do YAML.
8. Gera o inventário `poc.txt` com todos os POCs encontrados.
9. Atualiza automaticamente a seção de estatísticas deste `README.md`.

## Componentes do projeto

- `NucleiPocGather.py`: orquestra todo o pipeline de coleta, validação, organização e atualização.
- `DeWeight.py`: remove duplicidades adicionais comparando o conteúdo relevante dos templates YAML.
- `WirteREADME.py`: calcula estatísticas da coleção e atualiza a seção de métricas do `README.md`.
- `repo.txt`: lista dos repositórios GitHub usados como fonte de templates.
- `poc/`: diretório final com os templates organizados por categoria.
- `poc.txt`: inventário textual gerado com todos os caminhos de arquivos `.yaml` e `.yml`.

## Requisitos

- Python 3.10 ou superior
- `git`
- `unzip`
- Acesso de rede ao GitHub e à API pública do GitHub

Dependências Python:

```bash
pip install requests tqdm PyYAML
```

## Configuração

### 1. Clonar o repositório

```bash
git clone https://github.com/lianqingsec/NucleiPocGather.git
cd NucleiPocGather
```

### 2. Ajustar as fontes de coleta

Edite o arquivo `repo.txt` e mantenha uma URL por linha.

Exemplo:

```text
https://github.com/projectdiscovery/nuclei-templates
https://github.com/redteambrasil/nuclei-templates
```

### 3. Instalar dependências

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install requests tqdm PyYAML
```

## Execução local

Rode o pipeline completo com:

```bash
python NucleiPocGather.py
```

Saídas esperadas após a execução:

- `poc/` atualizado com os templates organizados por categoria
- `poc.txt` com a listagem de todos os arquivos YAML
- `README.md` com estatísticas atualizadas

## Implantação

### Opção 1. GitHub Actions

O repositório já possui o workflow `.github/workflows/main.yml`, que executa o script diariamente e também em `push` para `main`.

Passos recomendados:

1. Habilite `Actions` no repositório.
2. Em `Settings > Actions > General`, ajuste `Workflow permissions` para `Read and write permissions`.
3. Garanta que o branch padrão seja `main` ou ajuste o workflow conforme necessário.
4. Faça commit das alterações; o workflow instalará as dependências e executará `python NucleiPocGather.py`.

### Opção 2. Servidor Linux com agendamento

Em um host Linux, você pode implantar com `cron`.

Exemplo:

```bash
crontab -e
```

Agendamento diário às 09:00:

```cron
0 9 * * * cd /caminho/NucleiPocGather && /usr/bin/python3 NucleiPocGather.py >> /var/log/nucleipocgather.log 2>&1
```

## Estrutura de saída

```text
.
├── NucleiPocGather.py
├── DeWeight.py
├── WirteREADME.py
├── repo.txt
├── poc/
│   ├── cve/
│   ├── wordpress/
│   ├── auth/
│   └── ...
└── poc.txt
```

## Observações importantes

- O script foi traduzido para pt-BR nos textos exibidos ao usuário e na documentação.
- A lógica principal foi preservada.
- A atualização do `README.md` agora usa marcadores dedicados, o que deixa a documentação mais segura para futuras edições.
- O nome do módulo `WirteREADME.py` foi mantido para evitar impactos no fluxo atual.

## Estatísticas da coleção

<!-- stats:start -->
> **Atualização dos POCs do projeto:** `2026-08-21 13:28`

| ID | Tag | Quantidade | Diretório | Quantidade | Severidade | Quantidade |
|:---|:----|-----------:|:----------|-----------:|:-----------|-----------:|
| 1 | cve | 96295 | other | 56033 | medium | 40256 |
| 2 | wordpress | 89815 | cve | 50233 | low | 33837 |
| 3 | wp-plugin | 83128 | sql | 9099 | high | 28062 |
| 4 | candidate | 32134 | wordpress | 5944 | info | 27515 |
| 5 | low | 31381 | auth | 4588 | critical | 15050 |
| 6 | medium | 30790 | remote_code_execution | 3902 | unknown | 140 |
| 7 | tech | 17551 | detect | 1969 | informative | 17 |
| 8 | detect | 16656 | web | 1444 | hight | 15 |
| 9 | high | 16461 | microsoft | 1294 | meduim | 9 |
| 10 | service | 13833 | api | 1144 | cretical | 4 |

**10 diretórios, 149834 arquivos**
<!-- stats:end -->
