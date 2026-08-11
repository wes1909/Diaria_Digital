# Documentacao do Diaria Digital

## 1. Visao geral

Diaria Digital e um sistema web academico para demonstrar a digitalizacao do fluxo de diarias na Administracao Publica Municipal. O sistema cobre solicitacao, analise, aprovacao, viagem, prestacao de contas e conclusao do processo.

A aplicacao e demonstrativa e local. Ela nao deve ser tratada como sistema oficial de producao institucional.

## 2. Objetivo do sistema

O objetivo e apresentar um fluxo digital compreensivel para gestao de diarias, com calculo automatico de valores, controle de status, anexos, validacao por servidor responsavel e prestacao de contas.

## 3. Arquitetura e tecnologias

A aplicacao e desenvolvida com:

- Python;
- Flask;
- SQLite;
- HTML e templates Jinja2;
- CSS;
- JavaScript;
- Werkzeug para hash de senha;
- Gunicorn como dependencia para execucao em hospedagem.

O arquivo principal e `app.py`. Os templates ficam em `templates/`, arquivos estaticos em `static/`, anexos em `uploads/` e o banco local em `diarias.db`.

## 4. Perfis de usuario

O sistema possui dois perfis:

- `solicitante`: servidor que cria solicitacoes, acompanha o andamento, corrige pedidos e envia prestacao de contas.
- `validador`: servidor que cadastra usuarios, analisa solicitacoes, aprova, rejeita, solicita correcoes e avalia prestacoes de contas.

## 5. Autenticacao por CPF

O login usa CPF + senha. O CPF e normalizado por `normalize_cpf()`, ficando salvo apenas com digitos. A interface usa `static/cpf.js` para aplicar a mascara `000.000.000-00` no login e no formulario de usuarios.

A validacao de CPF em `validate_cpf()` confere presenca e 11 digitos apos normalizacao. A versao demonstrativa nao valida matematicamente os digitos verificadores. Os CPFs usados devem ser ficticios.

A coluna antiga `email` permanece no SQLite como legado tecnico, pois a tabela original possuia restricao `NOT NULL UNIQUE`. Ela nao e usada para login, pesquisa ou exibicao funcional.

## 6. Banco de dados

O banco usa SQLite e e inicializado/migrado por `init_db()` com `CREATE TABLE IF NOT EXISTS` e `ALTER TABLE` incremental.

### Tabela `users`

Campos principais:

- `id`: identificador interno.
- `name`: nome do usuario.
- `email`: campo legado tecnico.
- `cpf`: CPF normalizado usado para login.
- `password_hash`: hash da senha.
- `role`: `solicitante` ou `validador`.
- `daily_group`: grupo funcional usado no calculo da diaria.
- `registration`: matricula.
- `public_position`: cargo, emprego ou funcao.

### Tabela `requests`

Campos principais:

- `id`: identificador da solicitacao.
- `user_id`: usuario solicitante.
- `destination`: destino no formato `Cidade - UF`.
- `departure_date` e `return_date`: datas da viagem.
- `departure_time` e `return_time`: horarios previstos.
- `objective`: objetivo da viagem.
- `estimated_amount`: valor total calculado.
- `status`: status interno do processo.
- `validator_comment`: parecer do validador.
- `accountability_text`: resumo da prestacao de contas.
- `daily_group`: grupo funcional usado no calculo.
- `daily_range`: faixa automatica da viagem.
- `distance_km`: distancia considerada no momento do calculo.
- `base_amount`: valor-base da diaria.
- `overnight_count`: quantidade de pernoites informada e validada.
- `daily_quantity`: quantidade total de diarias calculada.
- `has_overnight`: campo legado/fallback.
- `daily_factor`: campo legado/fallback do fator antigo.
- `accountability_departure_time` e `accountability_arrival_time`: horarios informados na prestacao.
- `transport_mode`: meio de transporte.
- `departure_km` e `arrival_km`: quilometragem para veiculo oficial.
- `refund_amount`: valor a devolver.
- `created_at` e `updated_at`: datas de controle.

### Tabela `attachments`

Campos principais:

- `id`: identificador do anexo.
- `request_id`: solicitacao vinculada.
- `filename`: nome salvo no servidor.
- `original_name`: nome original do arquivo.
- `kind`: `solicitacao` ou `prestacao`.
- `attachment_type`: tipo auxiliar, como `deslocamento` ou `objetivo`.
- `uploaded_at`: data de envio.

## 7. Fluxo de solicitacao

O solicitante preenche estado, municipio, datas, horarios, quantidade de pernoites, objetivo e anexos opcionais. O backend recalcula o valor antes de salvar, usando grupo funcional, destino, distancia, faixa, duracao e pernoites.

Solicitacoes enviadas podem ser analisadas pelo validador, que aprova, rejeita ou solicita correcao. Quando ha correcao solicitada, o solicitante pode editar e reenviar.

## 8. Indicador visual das etapas

A tela de detalhes exibe uma linha visual com cinco macroetapas:

```text
Solicitacao -> Analise -> Viagem -> Prestacao de contas -> Conclusao
```

A funcao `get_process_progress(status)` mapeia cada status interno para a macroetapa visual. O indicador e apenas uma camada de orientacao; os status internos continuam controlando as regras do processo.

Para `rejeitada`, como o status nao armazena com seguranca em qual macroetapa a rejeicao ocorreu, o sistema apresenta processo interrompido e nao marca a conclusao como concluida automaticamente.

## 9. Regras de localidades e distancia

A lista de localidades fica em `static/localidades.js`, nas estruturas `localidadesNomesBrasil`, `distanciasLocalidadesKm` e `localidadesBrasil`.

A versao demonstrativa usa uma lista reduzida:

| UF | Municipio | Distancia aproximada |
|---|---|---:|
| SC | Lebon Regis | 0 km |
| SC | Cacador | 50 km |
| SC | Fraiburgo | 55 km |
| SC | Curitibanos | 85 km |
| SC | Campos Novos | 135 km |
| SC | Lages | 165 km |
| SC | Chapeco | 240 km |
| SC | Joinville | 300 km |
| SC | Blumenau | 300 km |
| SC | Florianopolis | 320 km |
| PR | Curitiba | 260 km |
| RS | Porto Alegre | 500 km |
| SP | Sao Paulo | 650 km |
| DF | Brasilia | 1.500 km |
| RJ | Rio de Janeiro | 1.102 km |

O usuario nao escolhe a faixa manualmente. O backend usa `get_destination_distance()` e `determine_daily_range()` para obter a distancia e classificar a viagem.

## 10. Grupos funcionais

Os grupos em `DAILY_GROUPS` sao:

- `agente_politico_comissionado`: Prefeito Municipal, Vice-Prefeito, Vereadores e Secretarios.
- `servidor_geral`: demais servidores efetivos, contratados, temporarios e cargos em comissao.

## 11. Valores-base

Os valores em `DAILY_RATES` sao:

| Faixa | Prefeito/Vice/Vereadores/Secretarios | Demais servidores |
|---|---:|---:|
| Ate 200 km dentro de SC | R$ 300,00 | R$ 300,00 |
| Acima de 200 km dentro de SC | R$ 600,00 | R$ 500,00 |
| Fora de SC ate 1.000 km ou Capital de SC | R$ 700,00 | R$ 800,00 |
| Acima de 1.000 km ou Capital Federal | R$ 1.500,00 | R$ 1.300,00 |

## 12. Calculo da duracao do afastamento

O backend combina `departure_date + departure_time` e `return_date + return_time` em `build_travel_datetimes()`. A funcao `validate_travel_period()` valida que a saida nao seja anterior ao dia atual e que o retorno seja posterior a saida. A duracao e calculada em horas.

## 13. Regra operacional para multiplos dias

A legislacao usada como referencia no projeto nao detalha uma formula completa para decompor afastamentos de varios dias. Por isso, a versao demonstrativa usa uma regra operacional isolada em `calculate_daily_quantity()`.

A regra divide o afastamento em blocos completos de 24 horas e eventual periodo residual. Ela foi documentada como decisao operacional da demonstracao, nao como transcricao literal da lei.

## 14. Quantidade de pernoites

O campo visivel e `Quantidade de pernoites`. A funcao `validate_overnight_count()` exige numero inteiro maior ou igual a zero, limita ao maximo possivel entre as datas e bloqueia pernoite maior que zero quando saida e retorno ocorrem no mesmo dia.

O sistema nao presume que mudanca de data significa pernoite.

## 15. Calculo da quantidade de diarias

A funcao `calculate_daily_quantity(duration_hours, overnight_count)` aplica:

- cada bloco completo de 24 horas = 1,00 diaria;
- residual superior a 12 horas com pernoite associado = 1,00 diaria;
- residual superior a 12 horas sem pernoite associado = 0,70 diaria;
- residual inferior a 12 horas sem pernoite associado = 0,50 diaria.

Blocos completos de 24 horas consomem no maximo um pernoite cada. Se os pernoites informados excedem os blocos completos, o residual e considerado com pernoite.

O caso exatamente igual a 12 horas e tratado pela constante `EXACT_12_HOURS_DAILY_FRACTION = 0.70`, como decisao operacional demonstrativa.

## 16. Calculo do valor total

A funcao `calculate_daily_amount()` busca o valor-base conforme grupo funcional e faixa, e calcula:

```text
valor total = valor-base * daily_quantity
```

O valor enviado pelo navegador nao e confiado como valor definitivo. O Flask recalcula antes de salvar.

## 17. Prestacao de contas

A prestacao fica disponivel quando a viagem esta aprovada ou quando ha correcao de prestacao solicitada. O solicitante informa resumo, horarios, meio de transporte, valor a devolver e comprovantes.

Quando ha valor a devolver menor que o valor recebido, o sistema exige comprovantes de deslocamento e comprovantes do cumprimento do objetivo. O validador pode aprovar, aprovar com ressalvas, rejeitar ou solicitar correcao.

## 18. Regra das 48 horas

`ACCOUNTABILITY_DEADLINE_DAYS = 2`. A funcao `get_overdue_accountability()` identifica solicitacoes aprovadas com retorno ha pelo menos dois dias e sem prestacao, ou com status `prestacao_correcao_solicitada`.

Enquanto houver pendencia vencida, o painel do solicitante exibe o botao de nova solicitacao como bloqueado, mostra aviso da pendencia e link para abrir a solicitacao pendente. A rota `/solicitacoes/nova` tambem bloqueia a criacao e redireciona para a pendencia.

## 19. Status internos

Status em `STATUS_LABELS`:

| Status | Significado |
|---|---|
| `rascunho` | Pedido ainda em preparacao. |
| `enviada` | Solicitacao enviada para analise. |
| `aprovada` | Viagem aprovada. |
| `correcao_solicitada` | Correcao solicitada antes da aprovacao. |
| `corrigida` | Solicitacao corrigida e reenviada. |
| `prestacao_enviada` | Prestacao enviada para avaliacao. |
| `prestacao_correcao_solicitada` | Correcao solicitada na prestacao. |
| `prestacao_corrigida` | Prestacao corrigida e reenviada. |
| `prestacao_aprovada` | Prestacao aprovada. |
| `prestacao_aprovada_ressalvas` | Prestacao aprovada com ressalvas. |
| `rejeitada` | Processo rejeitado. |

## 20. Tooltips e apoio a usabilidade

A interface possui tooltips em campos com regras menos obvias. O arquivo `static/tooltips.js` permite exibir as explicacoes por mouse, foco de teclado e toque/click. O CSS fica em `static/estilos.css`.

## 21. Pagina inicial

Usuarios nao autenticados acessam `templates/index.html`, uma pagina inicial com apresentacao do sistema, fluxo, perfis, aviso academico e botao para login. Usuarios autenticados sao redirecionados pela rota `/` ao painel correspondente.

## 22. Usuarios demonstrativos

Usuarios atualmente disponiveis no banco demonstrativo:

- Solicitante com pendencia: CPF `111.111.111-11`, senha `123456`.
- Validador: CPF `222.222.222-22`, senha `123456`.
- Solicitante sem pendencia: CPF `333.333.333-33`, senha `123456`.

As contas sao ficticias e existem apenas para demonstracao.

## 23. Estrutura principal dos arquivos

- `app.py`: rotas, regras de negocio, migracoes SQLite, validacoes e calculo definitivo.
- `templates/index.html`: pagina inicial publica.
- `templates/base.html`: estrutura comum das paginas.
- `templates/login.html`: login por CPF.
- `templates/request_form.html`: nova solicitacao/correcao de solicitacao.
- `templates/request_detail.html`: detalhes, indicador visual, anexos e acoes.
- `templates/requester_dashboard.html`: painel do solicitante.
- `templates/validator_dashboard.html`: painel do validador.
- `templates/form_prestacao.html`: prestacao de contas.
- `templates/users_list.html`: listagem de usuarios.
- `templates/user_form.html`: cadastro/edicao de usuarios.
- `static/estilos.css`: estilos e responsividade.
- `static/localidades.js`: destinos e distancias.
- `static/calculo_diarias.js`: previa visual do calculo.
- `static/prestacao.js`: comportamento do formulario de prestacao.
- `static/restricoes_datas.js`: apoio visual para datas.
- `static/horarios_24h.js`: mascara/validacao visual de horarios.
- `static/cpf.js`: mascara de CPF.
- `static/tooltips.js`: tooltips.
- `static/acessibilidade.js`: alto contraste.
- `static/campos_obrigatorios.js`: apoio visual de campos obrigatorios.

## 24. Principais funcoes do backend

- `normalize_cpf()`, `validate_cpf()`, `format_cpf()`: tratamento de CPF.
- `current_user()`, `login_required()`, `role_required()`: sessao e permissao.
- `load_locality_distances()`, `get_destination_distance()`, `determine_daily_range()`: destinos, distancias e faixas.
- `parse_form_date()`, `parse_form_time()`, `build_travel_datetimes()`, `validate_travel_period()`: datas, horarios e duracao.
- `calculate_max_overnights()`, `validate_overnight_count()`: pernoites.
- `calculate_daily_quantity()`, `calculate_residual_daily_fraction()`: quantidade de diarias.
- `calculate_daily_amount()`, `calculate_request_amount()`: valor-base e valor total.
- `get_overdue_accountability()`: pendencia de prestacao apos 48 horas.
- `get_process_progress()`: mapeamento visual de status para macroetapas.
- `validate_accountability_form()`, `validate_accountability_files()`: prestacao de contas.
- `save_attachment()`, `get_attachments()`: anexos.

## 25. Principais arquivos JavaScript

- `localidades.js`: popula estado/cidade, monta destino e exibe distancia aproximada.
- `calculo_diarias.js`: previa do valor-base, duracao, pernoites, quantidade de diarias e valor total.
- `acessibilidade.js`: alternancia de alto contraste.
- `cpf.js`: mascara de CPF.
- `tooltips.js`: abertura/fechamento de tooltips.
- `restricoes_datas.js`: apoio aos campos de data.
- `horarios_24h.js`: entrada de horas no formato 24h.
- `prestacao.js`: comportamento dos campos da prestacao de contas.
- `campos_obrigatorios.js`: realce visual de obrigatoriedade.

## 26. Seguranca e limitacoes

A aplicacao e academica. Para producao seriam necessarios reforcos de seguranca, auditoria, controle de acesso a arquivos, protecao de dados pessoais, validacoes oficiais, politica de backups, armazenamento apropriado de anexos e integracao com sistemas institucionais.

Nao utilize CPF real, dados bancarios reais ou documentos pessoais reais no ambiente demonstrativo.

## 27. Execucao local

Instale dependencias:

```bash
pip install -r requirements.txt
```

Execute:

```bash
python app.py
```

Acesse `http://127.0.0.1:5000`.

## 28. Deploy no Render

O projeto possui `gunicorn` em `requirements.txt`, o que permite execucao em hospedagem como Render quando configurada externamente. O repositorio atual nao possui arquivo `render.yaml`, `Procfile`, credenciais ou tokens de deploy.

## 29. Observacoes para demonstracao academica

Use apenas dados ficticios. O objetivo e demonstrar fluxo, usabilidade, calculo automatico, controle de status e prestacao de contas. Decisoes operacionais demonstrativas, como a decomposicao de multiplas diarias, foram isoladas para ajuste futuro caso exista regulamentacao administrativa especifica.
