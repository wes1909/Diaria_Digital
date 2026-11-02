# Documentação do Diária Digital

## 1. Visão geral

O Diária Digital é um sistema web acadêmico para demonstrar a digitalização do fluxo de diárias na Administração Pública Municipal. O sistema cobre solicitação, análise, aprovação, viagem, prestação de contas e conclusão do processo.

A aplicação é demonstrativa e foi disponibilizada em ambiente de hospedagem apenas para avaliação acadêmica. Ela não deve ser tratada como sistema oficial de produção institucional.

## 2. Objetivo do sistema

O objetivo é apresentar um fluxo digital compreensível para a gestão de diárias, com cálculo automático de valores, controle de status, anexos, validação por servidor responsável e prestação de contas.

## 3. Arquitetura e tecnologias

A aplicação é desenvolvida com:

- Python (desenvolvido com a versão 3.13);
- Flask;
- SQLite;
- HTML e templates Jinja2;
- CSS;
- JavaScript;
- Werkzeug para hash de senha;
- Gunicorn para execução em hospedagem.

O arquivo principal é `app.py`. Os templates ficam em `templates/`, os arquivos estáticos em `static/`, e `diarias.db` funciona como banco-modelo. Os bancos de trabalho e os anexos ficam em diretórios temporários isolados por sessão (seção 30).

## 4. Perfis de usuário

O sistema possui dois perfis:

- `solicitante`: representa o agente público beneficiário da diária. Pode cadastrar solicitações, acompanhar seu andamento, realizar correções e encaminhar a prestação de contas.
- `validador`: representa a autoridade máxima de uma secretaria ou um usuário por ela designado. Pode cadastrar novos usuários e analisar solicitações e prestações de contas. Nas solicitações, pode aprovar, rejeitar ou solicitar correções; nas prestações de contas, dispõe dessas mesmas opções e também da aprovação com ressalvas.

## 5. Autenticação por CPF

O login usa CPF e senha. O CPF é normalizado por `normalize_cpf()`, ficando salvo apenas com dígitos. A interface usa `static/cpf.js` para aplicar a máscara `000.000.000-00` no login e no formulário de usuários.

A validação de CPF em `validate_cpf()` confere a presença de 11 dígitos após a normalização. A versão demonstrativa não valida matematicamente os dígitos verificadores. Os CPFs usados devem ser fictícios.

A coluna antiga `email` permanece no SQLite como legado técnico, pois a tabela original possuía restrição `NOT NULL UNIQUE`. Ela é preenchida automaticamente no formato `<cpf>@cpf.local` e não é usada para login, pesquisa ou exibição.

## 6. Banco de dados

O banco usa SQLite. Cada cópia temporária é inicializada e migrada por `init_db(database_path)` com `CREATE TABLE IF NOT EXISTS` e `ALTER TABLE` incremental; o banco-modelo não é migrado durante as requisições normais.

### Tabela `users`

Campos principais:

- `id`: identificador interno.
- `name`: nome do usuário.
- `email`: campo legado técnico.
- `cpf`: CPF normalizado usado para login.
- `password_hash`: hash da senha.
- `role`: `solicitante` ou `validador`.
- `daily_group`: grupo funcional usado no cálculo da diária.
- `registration`: matrícula.
- `public_position`: cargo, emprego ou função.

### Tabela `requests`

Campos principais:

- `id`: identificador da solicitação.
- `user_id`: usuário solicitante.
- `destination`: destino no formato `Cidade - UF`.
- `departure_date` e `return_date`: datas da viagem.
- `departure_time` e `return_time`: horários previstos.
- `objective`: objetivo da viagem.
- `estimated_amount`: valor total calculado.
- `status`: status interno do processo.
- `validator_comment`: parecer do validador.
- `accountability_text`: resumo da prestação de contas.
- `daily_group`: grupo funcional usado no cálculo.
- `daily_range`: faixa automática da viagem.
- `distance_km`: distância considerada no momento do cálculo.
- `base_amount`: valor-base da diária.
- `overnight_count`: quantidade de pernoites informada e validada.
- `daily_quantity`: quantidade total de diárias calculada.
- `has_overnight`: campo mantido por compatibilidade; continua sendo gravado (1 quando há ao menos um pernoite).
- `daily_factor`: campo mantido por compatibilidade com o fator antigo; continua sendo gravado com o mesmo valor de `daily_quantity`.
- `accountability_departure_time` e `accountability_arrival_time`: horários informados na prestação.
- `transport_mode`: meio de transporte.
- `departure_km` e `arrival_km`: quilometragem para veículo oficial.
- `refund_amount`: valor a devolver.
- `created_at` e `updated_at`: datas de controle.

### Tabela `attachments`

Campos principais:

- `id`: identificador do anexo.
- `request_id`: solicitação vinculada.
- `filename`: nome salvo no servidor.
- `original_name`: nome original do arquivo.
- `kind`: `solicitacao` ou `prestacao`.
- `attachment_type`: tipo auxiliar, como `deslocamento` ou `objetivo`.
- `uploaded_at`: data de envio.

## 7. Fluxo de solicitação

O solicitante preenche estado, município, datas, horários, quantidade de pernoites, objetivo e anexos opcionais (PDF, PNG, JPG, JPEG, DOC ou DOCX). A data de saída não pode ser anterior à data atual, e o retorno deve ser posterior à saída. O backend recalcula o valor antes de salvar, usando grupo funcional, destino, distância, faixa, duração e pernoites.

A solicitação é gravada diretamente com o status `enviada` e pode ser analisada pelo validador, que aprova, rejeita ou solicita correção. Quando há correção solicitada, o solicitante pode editar e reenviar, e a solicitação passa ao status `corrigida`.

## 8. Indicador visual das etapas

A tela de detalhes exibe uma linha visual com cinco macroetapas:

```text
Solicitação -> Análise -> Viagem -> Prestação de contas -> Conclusão
```

A função `get_process_progress(status)` mapeia cada status interno para a macroetapa visual. O indicador é apenas uma camada de orientação; os status internos continuam controlando as regras do processo.

Para `rejeitada`, como o status não armazena com segurança em qual macroetapa a rejeição ocorreu, o sistema apresenta o processo como interrompido e não marca a conclusão como concluída automaticamente.

## 9. Regras de localidades e distância

A lista de localidades fica em `static/localidades.js`, nas estruturas `localidadesNomesBrasil`, `distanciasLocalidadesKm` e `localidadesBrasil`.

A versão demonstrativa usa uma lista reduzida, com a distância rodoviária aproximada a partir de Lebon Régis/SC:

| UF | Município | Distância aproximada |
|---|---|---:|
| SC | Lebon Régis | 0 km |
| SC | Caçador | 38 km |
| SC | Fraiburgo | 32 km |
| SC | Curitibanos | 55 km |
| SC | Campos Novos | 97 km |
| SC | Lages | 146 km |
| SC | Chapecó | 260 km |
| SC | Joinville | 288 km |
| SC | Blumenau | 260 km |
| SC | Florianópolis | 373 km |
| PR | Curitiba | 272 km |
| RS | Porto Alegre | 482 km |
| SP | São Paulo | 676 km |
| DF | Brasília | 1.661 km |
| RJ | Rio de Janeiro | 1.118 km |

O usuário não escolhe a faixa manualmente. O backend usa `get_destination_distance()` e `determine_daily_range()` para obter a distância e classificar a viagem. Florianópolis (capital do Estado) e Brasília (Capital Federal) são enquadradas pela regra de capital, independentemente da distância.

A função `load_locality_distances()` lê o objeto `distanciasLocalidadesKm` diretamente do arquivo `static/localidades.js`. Ao incluir ou alterar destinos, mantenha o mesmo formato (chaves `"UF|Município"` entre aspas e valores numéricos); caso contrário, o backend deixa de reconhecer as distâncias.

## 10. Grupos funcionais

Os grupos em `DAILY_GROUPS` são:

- `agente_politico_comissionado`: Prefeito Municipal, Vice-Prefeito, Vereadores e Secretários.
- `servidor_geral`: demais servidores efetivos, contratados, temporários e ocupantes de cargos em comissão.

Apesar do nome, a chave `agente_politico_comissionado` não inclui os ocupantes de cargos em comissão, que pertencem a `servidor_geral`. O nome foi mantido por compatibilidade com os registros já gravados no banco; `init_db()` inclusive transfere para `servidor_geral` os solicitantes comissionados que não sejam prefeito, vereador ou secretário.

## 11. Valores-base

Os valores em `DAILY_RATES` seguem a Lei Municipal nº 1.839/2026 de Lebon Régis:

| Faixa | Prefeito, Vice-Prefeito, Vereadores e Secretários | Demais servidores |
|---|---:|---:|
| Até 200 km dentro de SC | R$ 300,00 | R$ 300,00 |
| Acima de 200 km dentro de SC | R$ 600,00 | R$ 500,00 |
| Fora de SC até 1.000 km ou Capital de SC | R$ 700,00 | R$ 800,00 |
| Acima de 1.000 km ou Capital Federal | R$ 1.500,00 | R$ 1.300,00 |

## 12. Cálculo da duração do afastamento

O backend combina `departure_date + departure_time` e `return_date + return_time` em `build_travel_datetimes()`. A função `validate_travel_period()` valida que a saída não seja anterior ao dia atual e que o retorno seja posterior à saída. A duração é calculada em horas.

## 13. Regra operacional para múltiplos dias

A legislação usada como referência no projeto não detalha uma fórmula completa para decompor afastamentos de vários dias. Por isso, a versão demonstrativa usa uma regra operacional isolada em `calculate_daily_quantity()`.

A regra divide o afastamento em blocos completos de 24 horas e eventual período residual. Ela foi documentada como decisão operacional da demonstração, não como transcrição literal da lei.

## 14. Quantidade de pernoites

O campo visível é `Quantidade de pernoites`. A função `validate_overnight_count()` exige número inteiro maior ou igual a zero, limita a quantidade ao número de dias entre as datas de saída e de retorno e bloqueia pernoite maior que zero quando saída e retorno ocorrem no mesmo dia.

O sistema não presume que a mudança de data significa pernoite.

## 15. Cálculo da quantidade de diárias

A função `calculate_daily_quantity(duration_hours, overnight_count)` aplica:

- cada bloco completo de 24 horas = 1,00 diária;
- residual com pernoite associado = 1,00 diária, independentemente da duração do residual;
- residual superior a 12 horas sem pernoite associado = 0,70 diária;
- residual inferior a 12 horas sem pernoite associado = 0,50 diária;
- residual de exatamente 12 horas sem pernoite associado = 0,70 diária.

Blocos completos de 24 horas consomem no máximo um pernoite cada. Se os pernoites informados excedem os blocos completos, o residual é considerado com pernoite.

A lei prevê 1,00 diária para período superior a 12 horas com pernoite, mas não trata o período residual inferior a 12 horas com pernoite nem o caso de exatamente 12 horas. Esses dois casos são decisões operacionais da demonstração: o residual com pernoite vale sempre 1,00, e o caso de exatamente 12 horas usa a constante `EXACT_12_HOURS_DAILY_FRACTION = 0.70`.

## 16. Cálculo do valor total

A função `calculate_daily_amount()` busca o valor-base conforme grupo funcional e faixa e calcula:

```text
valor total = valor-base x daily_quantity
```

O formulário exibe uma prévia calculada no navegador por `static/calculo_diarias.js`, que repete a tabela de valores e as regras das seções 9 a 15. Esse valor não é confiado como definitivo: o Flask recalcula antes de salvar. Por isso, qualquer alteração de valores ou regras deve ser feita nos dois arquivos.

## 17. Prestação de contas

A prestação fica disponível quando a viagem está aprovada ou quando há correção de prestação solicitada. O solicitante informa resumo, horários de saída e de chegada, meio de transporte (aéreo, coletivo rodoviário, veículo próprio ou veículo oficial), valor a devolver e comprovantes. O valor recebido considerado é o valor total calculado na solicitação.

Quando o valor a devolver é menor que o valor recebido, o sistema exige de 1 a 10 comprovantes de deslocamento e de 1 a 10 comprovantes do cumprimento do objetivo, em PDF, PNG, JPG ou JPEG. Para veículo oficial, também são exigidos o KM de saída e o KM de chegada, e o KM de chegada não pode ser menor que o de saída.

Quando o valor a devolver é igual ao valor recebido (devolução integral, ou seja, viagem não realizada), apenas o resumo é obrigatório; horários, meio de transporte e comprovantes deixam de ser exigidos.

O validador pode aprovar, aprovar com ressalvas, rejeitar ou solicitar correção da prestação.

## 18. Prazo da prestação de contas

`ACCOUNTABILITY_DEADLINE_DAYS = 2`. A função `get_overdue_accountability()` identifica as solicitações aprovadas cujo retorno ocorreu há pelo menos dois dias e que ainda não possuem prestação, bem como as que estão com status `prestacao_correcao_solicitada` na mesma condição. A contagem compara apenas a data de retorno com a data atual, sem considerar o horário. Essa regra simplifica o tratamento do prazo e não contempla integralmente a previsão da Lei Municipal nº 1.839/2026 quanto ao primeiro dia útil subsequente.

Enquanto houver pendência vencida, o painel do solicitante exibe o botão de nova solicitação como bloqueado, mostra aviso da pendência e link para abrir a solicitação pendente. A rota `/solicitacoes/nova` também bloqueia a criação e redireciona para a pendência.

## 19. Status internos

Status em `STATUS_LABELS`:

| Status | Significado |
|---|---|
| `rascunho` | Previsto no modelo, mas não utilizado nesta versão (a solicitação é gravada diretamente como `enviada`). |
| `enviada` | Solicitação enviada para análise. |
| `aprovada` | Viagem aprovada. |
| `correcao_solicitada` | Correção solicitada antes da aprovação. |
| `corrigida` | Solicitação corrigida e reenviada. |
| `prestacao_enviada` | Prestação enviada para avaliação. |
| `prestacao_correcao_solicitada` | Correção solicitada na prestação. |
| `prestacao_corrigida` | Prestação corrigida e reenviada. |
| `prestacao_aprovada` | Prestação aprovada. |
| `prestacao_aprovada_ressalvas` | Prestação aprovada com ressalvas. |
| `rejeitada` | Processo rejeitado. |

As ações disponíveis ao validador em cada status são definidas em `templates/request_detail.html`: análise da solicitação nos status `enviada`, `corrigida`, `correcao_solicitada` e `aprovada` (sem a opção de aprovar novamente quando já aprovada), e análise da prestação nos status `prestacao_enviada` e `prestacao_corrigida`.

## 20. Recursos de apoio ao preenchimento

A interface indica os campos obrigatórios (`static/campos_obrigatorios.js`), aplica máscaras de preenchimento para CPF e horários (`static/cpf.js` e `static/horarios_24h.js`) e oferece a opção de alto contraste (`static/acessibilidade.js`), que fica salva no navegador. Também possui tooltips em campos com regras menos óbvias. A exibição por mouse e por foco de teclado é feita pelo CSS em `static/estilos.css`; o arquivo `static/tooltips.js` acrescenta a abertura por toque ou clique e o fechamento pela tecla Esc.

## 21. Página inicial

Usuários não autenticados acessam `templates/index.html`, uma página inicial com apresentação do sistema, fluxo, perfis, aviso acadêmico e botão para login. Usuários autenticados são redirecionados pela rota `/` ao painel correspondente.

## 22. Usuários demonstrativos

Usuários disponíveis no banco demonstrativo:

- Solicitante com pendência: CPF `111.111.111-11`, senha `123456`.
- Validador: CPF `222.222.222-22`, senha `123456`.
- Solicitante sem pendência: CPF `333.333.333-33`, senha `123456`.

As contas são fictícias e existem apenas para demonstração.

## 23. Estrutura principal dos arquivos

- `app.py`: rotas, regras de negócio, migrações SQLite, validações e cálculo definitivo.
- `templates/index.html`: página inicial pública.
- `templates/base.html`: estrutura comum das páginas.
- `templates/login.html`: login por CPF.
- `templates/request_form.html`: nova solicitação e correção de solicitação.
- `templates/request_detail.html`: detalhes, indicador visual, anexos e ações.
- `templates/requester_dashboard.html`: painel do solicitante.
- `templates/validator_dashboard.html`: painel do validador.
- `templates/form_prestacao.html`: prestação de contas.
- `templates/users_list.html`: listagem de usuários.
- `templates/user_form.html`: cadastro e edição de usuários.
- `static/estilos.css`: estilos e responsividade.
- `static/localidades.js`: destinos e distâncias.
- `static/calculo_diarias.js`: prévia visual do cálculo.
- `static/prestacao.js`: comportamento do formulário de prestação.
- `static/restricoes_datas.js`: apoio visual para datas.
- `static/horarios_24h.js`: máscara e validação visual de horários.
- `static/cpf.js`: máscara de CPF.
- `static/tooltips.js`: tooltips.
- `static/acessibilidade.js`: alto contraste.
- `static/grupo_funcional.js`: exibição do grupo funcional no cadastro de usuários.
- `static/campos_obrigatorios.js`: apoio visual de campos obrigatórios.

## 24. Principais funções do backend

- `normalize_cpf()`, `validate_cpf()`, `format_cpf()`: tratamento de CPF.
- `current_user()`, `login_required()`, `role_required()`: sessão e permissão.
- `load_locality_distances()`, `get_destination_distance()`, `determine_daily_range()`: destinos, distâncias e faixas.
- `parse_form_date()`, `parse_form_time()`, `build_travel_datetimes()`, `validate_travel_period()`: datas, horários e duração.
- `calculate_max_overnights()`, `validate_overnight_count()`: pernoites.
- `calculate_daily_quantity()`, `calculate_residual_daily_fraction()`: quantidade de diárias.
- `calculate_daily_amount()`, `calculate_request_amount()`: valor-base e valor total.
- `get_overdue_accountability()`: pendência de prestação após o prazo da seção 18.
- `get_process_progress()`: mapeamento visual de status para macroetapas.
- `validate_accountability_form()`, `validate_accountability_files()`: prestação de contas.
- `save_attachment()`, `get_attachments()`: anexos.
- `create_demo_environment()`, `prepare_demo_scenarios()`, `cleanup_old_demo_environments()`: ambiente demonstrativo isolado por sessão (seção 30).

## 25. Principais arquivos JavaScript

- `localidades.js`: popula estado e cidade, monta o destino e exibe a distância aproximada.
- `calculo_diarias.js`: prévia do valor-base, duração, pernoites, quantidade de diárias e valor total.
- `acessibilidade.js`: alternância de alto contraste.
- `cpf.js`: máscara de CPF.
- `tooltips.js`: abertura e fechamento de tooltips.
- `restricoes_datas.js`: apoio aos campos de data.
- `horarios_24h.js`: entrada de horas no formato 24h.
- `prestacao.js`: comportamento dos campos da prestação de contas.
- `grupo_funcional.js`: exibe o grupo funcional somente para o perfil solicitante.
- `campos_obrigatorios.js`: realce visual de obrigatoriedade.

## 26. Segurança e limitações

A aplicação é acadêmica. Uma eventual implantação na Administração Municipal exigiria adequações na infraestrutura, especialmente quanto ao armazenamento permanente dos dados e documentos, mecanismos de segurança, auditoria, cópias de segurança, controle de acesso a arquivos, proteção de dados pessoais, validações oficiais e integração com os sistemas institucionais.

A chave de sessão (`SECRET_KEY`) definida em `app.py` é de uso exclusivamente acadêmico e deve ser substituída por um valor secreto em qualquer uso fora da demonstração.

Não utilize CPF real, dados bancários reais ou documentos pessoais reais no ambiente demonstrativo.

## 27. Execução local

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
python app.py
```

Acesse `http://127.0.0.1:5000`.

A execução por `python app.py` utiliza o servidor de desenvolvimento do Flask em modo de depuração e destina-se apenas ao uso local.

## 28. Deploy no Render

A aplicação está hospedada no Render, onde é executada pelo `gunicorn`, incluído em `requirements.txt`. Como o repositório não possui os arquivos `Procfile` ou `render.yaml`, o comando de inicialização (`gunicorn app:app`) foi configurado diretamente no painel do Render. O repositório não contém tokens ou credenciais de acesso à hospedagem.

## 29. Observações para demonstração acadêmica

Use apenas dados fictícios. O objetivo é demonstrar fluxo, usabilidade, cálculo automático, controle de status e prestação de contas. Decisões operacionais demonstrativas, como a decomposição de múltiplas diárias, foram isoladas para ajuste futuro caso exista regulamentação administrativa específica.

## 30. Arquitetura da demonstração isolada por sessão

Na versão destinada à avaliação acadêmica, `diarias.db` é exclusivamente o banco-modelo. A aplicação nunca o abre implicitamente em uma rota normal: `get_db()` resolve a cópia associada a `session["demo_environment_id"]`, enquanto `init_db(database_path)` recebe sempre o caminho explícito que será preparado.

No primeiro acesso de uma sessão, `get_demo_environment_id()` cria um UUID hexadecimal de 32 caracteres exclusivamente no servidor. O valor é validado antes de selecionar qualquer diretório, e o cookie do Flask guarda apenas esse identificador e, durante a autenticação, o `user_id`. CPF, IP, nome e user-agent não participam do caminho. A sessão é permanente por 7 dias; fechar e reabrir normalmente o mesmo navegador recupera o ambiente enquanto o cookie e os arquivos temporários existirem.

`create_demo_environment()` copia o modelo com `shutil.copy2()` para `<temp>/diaria_digital_demo/<id>/diarias.db`, atualiza o schema dessa cópia e prepara os cenários com `prepare_demo_scenarios()`. O registro aprovado e sem prestação mais recente do CPF 111 é reutilizado; suas datas passam a ser saída quatro dias antes e retorno três dias antes da data corrente. Se ele não existir, um registro demonstrativo é criado. Para o CPF 333, qualquer registro que já começaria vencido tem o retorno trazido para a data atual, preservando-o livre para uma nova solicitação.

Os três CPFs demonstrativos são conferidos sem duplicação e recebem a senha `123456`. O login cria o ambiente antes de consultar o usuário. Login e logout preservam `demo_environment_id`, o que permite criar uma solicitação como solicitante, sair, entrar como validador e continuar no mesmo banco isolado.

`get_demo_upload_folder()` direciona gravação e download para `<temp>/diaria_digital_demo/<id>/uploads/`. O projeto atual não contém pasta-base de uploads nem registros de anexos no banco-modelo. Mesmo assim, a preparação copia somente nomes seguros que estejam referenciados pela tabela `attachments`, caso o modelo passe a incluí-los no futuro.

**Reiniciar demonstração** é uma operação POST com confirmação no navegador e é o mecanismo explícito de restauração. Ela remove somente o diretório UUID validado da sessão atual, limpa a autenticação e o identificador e redireciona ao login; o próximo acesso recria o estado inicial. Diretórios UUID sem utilização há mais de 7 dias são removidos quando outro ambiente é criado, sem tarefa agendada e sem tocar no ambiente atual, em links simbólicos ou no banco-modelo. O acesso normal atualiza a data de atividade do diretório.

Os bancos e uploads temporários não são persistentes. Os 7 dias são o prazo de retenção da aplicação enquanto o armazenamento temporário da instância permanecer disponível; reinícios da infraestrutura do Render podem eliminar os dados antes desse prazo, e os ambientes são recriados automaticamente no acesso seguinte. Esse desenho atende exclusivamente à demonstração acadêmica simultânea e não deve ser tratado como arquitetura recomendada para produção institucional.
