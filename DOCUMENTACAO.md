# Documentacao do Sistema de Gestao de Diarias

Este documento explica a organizacao do sistema e o significado dos principais nomes tecnicos usados no codigo. O objetivo e facilitar a apresentacao academica sem alterar nomes internos que seguem convencoes comuns de programacao.

## Objetivo do Sistema

O sistema permite gerenciar solicitacoes de diarias em ambiente academico/local, com fluxo de cadastro da viagem, validacao, prestacao de contas e avaliacao final.

## Perfis do Sistema

- **Servidor solicitante**: cadastra solicitacoes de diaria, corrige solicitacoes quando solicitado, envia prestacao de contas e acompanha o status.
- **Servidor validador**: cadastra e edita servidores, analisa solicitacoes, aprova, rejeita, solicita correcoes e avalia prestacoes de contas.

## Fluxo Principal

1. O solicitante acessa o sistema.
2. Cadastra uma solicitacao com destino, datas, horarios, pernoite, objetivo e anexos opcionais.
3. O sistema identifica a faixa da viagem automaticamente a partir do municipio escolhido e da distancia cadastrada.
4. O backend calcula valor-base, fator aplicavel e valor total estimado antes de salvar.
5. O validador analisa a solicitacao com acesso ao destino, distancia, horarios, duracao, faixa, fator, valor-base e valor total.
6. O validador pode aprovar, rejeitar ou solicitar correcao.
7. Apos aprovacao da viagem, o solicitante envia a prestacao de contas.
8. O validador avalia a prestacao e pode aprovar, aprovar com ressalvas, rejeitar ou solicitar correcao.

## Grupos Funcionais

- `agente_politico_comissionado`: Prefeito Municipal, Vice-Prefeito, Vereadores e Secretarios.
- `servidor_geral`: demais servidores publicos efetivos, contratados, temporarios e ocupantes de cargos em comissao.

O identificador antigo `agente_politico_comissionado` foi preservado para compatibilidade com usuarios e registros existentes, mas cargos comissionados devem ser cadastrados no grupo `servidor_geral`.

## Valores das Diarias

| Faixa automatica | Grupo Prefeito/Vice/Vereadores/Secretarios | Grupo demais servidores |
|---|---:|---:|
| Ate 200 km dentro de Santa Catarina | R$ 300,00 | R$ 300,00 |
| Acima de 200 km dentro de Santa Catarina | R$ 600,00 | R$ 500,00 |
| Fora de Santa Catarina ate 1.000 km ou Capital de SC | R$ 700,00 | R$ 800,00 |
| Acima de 1.000 km ou Capital Federal | R$ 1.500,00 | R$ 1.300,00 |

## Enquadramento Automatico

O campo manual de enquadramento foi removido do formulario. O solicitante escolhe apenas estado e cidade. O sistema usa:

- UF do destino.
- Distancia rodoviaria aproximada em quilometros a partir de Lebon Regis/SC.
- Identificacao de Florianopolis/SC como Capital do Estado.
- Identificacao de Brasilia/DF como Capital Federal.

Regras:

- Destino em SC ate 200 km: `sc_ate_200`.
- Destino em SC acima de 200 km: `sc_acima_200`.
- Destino fora de SC ate 1.000 km ou Florianopolis/SC: `capital_sc_ou_fora_ate_1000`.
- Destino acima de 1.000 km ou Brasilia/DF: `capital_federal_ou_acima_1000`.

Se a distancia necessaria nao estiver cadastrada, o backend bloqueia o salvamento e informa que a distancia do municipio precisa ser preenchida.

## Duracao, Pernoite e Fator

A solicitacao possui agora `departure_time` e `return_time`, informados em campos HTML `time`. O backend combina data e hora de saida com data e hora de retorno e valida que o retorno seja posterior a saida.

A pergunta visivel passa a ser "Havera pernoite?". O fator e calculado pela funcao `calculate_daily_factor()`:

- Duracao superior a 12 horas com pernoite: fator 1,00.
- Duracao superior a 12 horas sem pernoite: fator 0,70.
- Duracao inferior a 12 horas sem pernoite: fator 0,50.

A legislacao informada nao definiu explicitamente o caso de duracao exatamente igual a 12 horas nem o tratamento detalhado para viagens de multiplos dias. Por isso, a regra foi mantida isolada no backend para ajuste posterior. O sistema nao cria multiplicador juridico adicional para multiplos dias sem definicao legal expressa.

## Banco de Dados

O `init_db()` continua usando migracoes incrementais com `ALTER TABLE`, preservando bancos SQLite existentes. Foram adicionadas colunas na tabela `requests`:

| Coluna | Finalidade |
|---|---|
| `departure_time` | Hora de saida prevista |
| `return_time` | Hora prevista de retorno |
| `distance_km` | Copia historica da distancia usada no calculo |
| `daily_factor` | Fator aplicado conforme duracao e pernoite |
| `base_amount` | Valor-base da diaria usado no calculo |

A copia da distancia na solicitacao preserva o historico caso a distancia cadastrada para um municipio seja alterada futuramente.

## Municipios e Distancias

A fonte de municipios permanece em `static/localidades.js`. A estrutura original de nomes por UF foi preservada e enriquecida em tempo de execucao para que cada municipio possua:

- `nome`
- `uf`
- `cidade`
- `uf`
- `distancia_km`
- `capitalEstadual`
- `capitalFederal`

As distancias ficam no mapa `distanciasLocalidadesKm` no mesmo arquivo. Para adicionar um novo municipio, inclua o nome na lista da UF correspondente e adicione sua distancia no mapa:

```js
const distanciasLocalidadesKm = {
    "SC|Lebon Regis": 0,
    "SC|Novo Municipio": 145
};
```

Nao foram inseridas distancias ficticias. Os municipios que nao possuem valor confiavel no projeto permanecem com `distancia_km: null` e precisam ser preenchidos posteriormente.

## Principais Arquivos

- `app.py`: rotas, regras de negocio, migracoes SQLite, validacoes e calculo definitivo no backend.
- `templates/request_form.html`: formulario de solicitacao com destino, datas, horarios, pernoite e resumo de calculo.
- `templates/request_detail.html`: tela de detalhe, avaliacao e conferencia do calculo.
- `templates/requester_dashboard.html`: painel do solicitante.
- `templates/validator_dashboard.html`: painel do validador.
- `templates/form_prestacao.html`: formulario de prestacao de contas.
- `templates/users_list.html`: listagem de servidores.
- `templates/user_form.html`: cadastro e edicao de servidores.
- `static/localidades.js`: estados, municipios e distancias cadastradas.
- `static/calculo_diarias.js`: pre-visualizacao do calculo na interface.
- `static/restricoes_datas.js`: regras visuais para datas da solicitacao.
- `static/prestacao.js`: mascaras e regras visuais da prestacao de contas.
- `static/campos_obrigatorios.js`: validacao visual de campos obrigatorios.
- `static/estilos.css`: estilos e responsividade.

## Glossario de Nomes Tecnicos

| Nome no codigo | Significado |
|---|---|
| `user` | Usuario ou servidor cadastrado |
| `request` | Solicitacao de diaria |
| `daily_request` | Solicitacao carregada para exibicao ou edicao |
| `accountability` | Prestacao de contas |
| `validator` | Servidor validador |
| `requester` | Servidor solicitante |
| `destination` | Destino da viagem |
| `departure_date` | Data de saida |
| `departure_time` | Hora de saida |
| `return_date` | Data de retorno |
| `return_time` | Hora prevista de retorno |
| `distance_km` | Distancia usada no calculo |
| `daily_group` | Grupo funcional do servidor |
| `daily_range` | Faixa automatica da viagem |
| `daily_factor` | Fator aplicado pela duracao/pernoite |
| `base_amount` | Valor-base da faixa |
| `estimated_amount` | Valor total calculado |
| `has_overnight` | Indica se havera pernoite |
| `validator_comment` | Parecer do validador |
| `accountability_text` | Resumo da prestacao de contas |
| `transport_mode` | Meio de transporte utilizado |
| `departure_km` | Quilometragem de saida na prestacao |
| `arrival_km` | Quilometragem de chegada na prestacao |
| `refund_amount` | Valor a devolver |
| `attachments` | Anexos ou comprovantes |
| `registration` | Matricula do servidor |
| `public_position` | Cargo, emprego ou funcao |

## Status Utilizados

| Status interno | Texto exibido |
|---|---|
| `enviada` | Enviada |
| `aprovada` | Viagem Aprovada |
| `correcao_solicitada` | Correcao Solicitada |
| `corrigida` | Corrigida |
| `prestacao_enviada` | Prestacao Enviada |
| `prestacao_correcao_solicitada` | Correcao da Prestacao Solicitada |
| `prestacao_corrigida` | Prestacao Corrigida |
| `prestacao_aprovada` | Prestacao Aprovada |
| `prestacao_aprovada_ressalvas` | Prestacao Aprovada com Ressalvas |
| `rejeitada` | Rejeitada |

## Observacao Sobre Variaveis em Ingles

Alguns nomes internos foram mantidos em ingles por seguirem padroes comuns de desenvolvimento web, especialmente em Flask, HTML, JavaScript e bancos de dados. A interface, mensagens, regras e documentacao estao em portugues, priorizando a compreensao pelo usuario final e pela banca avaliadora.

O sistema encontra-se hospedado em ambiente gratuito de nuvem, sujeito a inicializacao sob demanda.
