# Documentação do Sistema de Gestão de Diárias

Este documento explica a organização do sistema e o significado dos principais nomes técnicos usados no código. O objetivo é facilitar a apresentação acadêmica sem alterar nomes internos que seguem convenções comuns de programação.

## Objetivo do Sistema

O sistema permite gerenciar solicitações de diárias em ambiente acadêmico/local, com fluxo de cadastro da viagem, validação, prestação de contas e avaliação final.

## Perfis do Sistema

- **Servidor solicitante**: cadastra solicitações de diária, corrige solicitações quando solicitado, envia prestação de contas e acompanha o status.
- **Servidor validador**: cadastra e edita servidores, analisa solicitações, aprova, rejeita, solicita correções e avalia prestações de contas.

## Fluxo Principal

1. O solicitante acessa o sistema.
2. Cadastra uma solicitação de diária com destino, datas, objetivo, enquadramento e anexos opcionais.
3. O sistema calcula o valor da diária conforme grupo do servidor, faixa da viagem, estadia e quantidade de dias.
4. O validador analisa a solicitação.
5. O validador pode aprovar, rejeitar ou solicitar correção.
6. Após aprovação da viagem, o solicitante envia a prestação de contas.
7. O validador avalia a prestação e pode aprovar, aprovar com ressalvas, rejeitar ou solicitar correção.

## Regras Implementadas

- O grupo de diária é definido no cadastro do servidor, não escolhido na solicitação.
- A data de saída da viagem não pode ser anterior à data atual.
- A data de retorno não pode ser anterior à data de saída.
- O valor da diária é calculado pela regra de enquadramento e multiplicado pela quantidade de dias.
- Sem estadia, o valor considerado é metade da diária.
- O solicitante fica bloqueado para novas solicitações se tiver prestação de contas pendente após 48 horas do retorno.
- Na prestação, se o servidor devolver o valor integral recebido, só precisa informar o valor devolvido e o resumo da viagem.
- Para veículo oficial, devem ser informados KM de saída e KM de chegada; o KM de chegada não pode ser menor.
- Comprovantes de prestação são separados entre deslocamento e cumprimento do objetivo.

## Principais Arquivos

- `app.py`: concentra rotas, regras de negócio, banco SQLite e validações do backend.
- `templates/request_form.html`: formulário de solicitação de diária.
- `templates/request_detail.html`: tela de detalhe, avaliação e acompanhamento da solicitação.
- `templates/form_prestacao.html`: formulário de prestação de contas.
- `templates/users_list.html`: listagem de servidores.
- `templates/user_form.html`: cadastro e edição de servidores.
- `static/calculo_diarias.js`: cálculo visual do valor total da diária no formulário.
- `static/restricoes_datas.js`: regras visuais para datas da solicitação.
- `static/prestacao.js`: máscaras e regras visuais da prestação de contas.
- `static/localidades.js`: estados e cidades usados no destino.
- `static/campos_obrigatorios.js`: validação visual de campos obrigatórios.
- `static/estilos.css`: estilos e responsividade.

## Glossário de Nomes Técnicos

| Nome no código | Significado em português |
|---|---|
| `user` | Usuário ou servidor cadastrado |
| `request` | Solicitação de diária |
| `daily_request` | Solicitação de diária carregada para exibição ou edição |
| `accountability` | Prestação de contas |
| `validator` | Servidor validador |
| `requester` | Servidor solicitante |
| `status` | Situação atual da solicitação |
| `destination` | Destino da viagem |
| `departure_date` | Data de saída |
| `return_date` | Data de retorno |
| `estimated_amount` | Valor calculado/recebido da diária |
| `daily_group` | Grupo de enquadramento do servidor |
| `daily_range` | Faixa de enquadramento da viagem |
| `has_overnight` | Indica se houve estadia no local |
| `validator_comment` | Parecer do validador |
| `accountability_text` | Resumo/relato da prestação de contas |
| `transport_mode` | Meio de transporte utilizado |
| `departure_km` | Quilometragem de saída |
| `arrival_km` | Quilometragem de chegada |
| `refund_amount` | Valor a devolver |
| `attachments` | Anexos ou comprovantes |
| `registration` | Matrícula do servidor |
| `public_position` | Cargo, emprego ou função |

## Status Utilizados

| Status interno | Texto exibido |
|---|---|
| `enviada` | Enviada |
| `aprovada` | Viagem Aprovada |
| `correcao_solicitada` | Correção Solicitada |
| `corrigida` | Corrigida |
| `prestacao_enviada` | Prestação Enviada |
| `prestacao_correcao_solicitada` | Correção da Prestação Solicitada |
| `prestacao_corrigida` | Prestação Corrigida |
| `prestacao_aprovada` | Prestação Aprovada |
| `prestacao_aprovada_ressalvas` | Prestação Aprovada com Ressalvas |
| `rejeitada` | Rejeitada |

## Observação Sobre Variáveis em Inglês

Alguns nomes internos foram mantidos em inglês por seguirem padrões comuns de desenvolvimento web, especialmente em Flask, HTML, JavaScript e bancos de dados. A interface, mensagens, regras e documentação estão em português, priorizando a compreensão pelo usuário final e pela banca avaliadora.
