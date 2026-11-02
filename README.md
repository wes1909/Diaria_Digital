# Diária Digital

O Diária Digital é um sistema web acadêmico desenvolvido para demonstrar a digitalização do processo de solicitação, análise, aprovação, viagem e prestação de contas de diárias na Administração Pública Municipal.

O projeto é um ambiente demonstrativo. Ele não representa um sistema oficialmente implantado em produção institucional, e os dados utilizados devem ser fictícios.

## Tecnologias

- Python (desenvolvido com a versão 3.13)
- Flask
- SQLite
- HTML (templates Jinja2)
- CSS
- JavaScript
- Gunicorn

As dependências Python estão listadas em `requirements.txt`.

## Perfis de acesso

- **Servidor Solicitante**: representa o agente público beneficiário da diária. Pode cadastrar solicitações, acompanhar seu andamento, realizar correções e encaminhar a prestação de contas.
- **Servidor Validador**: representa a autoridade máxima de uma secretaria ou um usuário por ela designado. Pode cadastrar novos usuários e analisar solicitações e prestações de contas. Nas solicitações, pode aprovar, rejeitar ou solicitar correções; nas prestações de contas, dispõe dessas mesmas opções e também da aprovação com ressalvas.

## Usuários demonstrativos

- **Solicitante com pendência**: CPF `111.111.111-11`, senha `123456`.
  Demonstra o bloqueio por prestação de contas vencida.
- **Validador**: CPF `222.222.222-22`, senha `123456`.
  Demonstra o painel de análise, validação e cadastro de usuários.
- **Solicitante sem pendência**: CPF `333.333.333-33`, senha `123456`.
  Demonstra o fluxo normal de uma nova solicitação.

## Autenticação

O acesso ao sistema é feito por CPF e senha. O CPF é usado como identificador de acesso, armazenado internamente apenas com números e exibido na interface com a máscara `000.000.000-00`. A versão demonstrativa verifica apenas se o CPF possui 11 dígitos, sem validar os dígitos verificadores.

Os CPFs demonstrativos são fictícios. Não utilize CPF real, dados bancários reais ou documentos pessoais reais neste ambiente.

## Fluxo principal

O sistema apresenta uma linha visual de progresso com cinco macroetapas:

```text
Solicitação -> Análise -> Viagem -> Prestação de contas -> Conclusão
```

Essa linha é apenas uma representação visual simplificada. Os status internos são mais detalhados e controlam as permissões, transições, correções, aprovações e rejeições.

## Solicitação de diária

O solicitante informa:

- estado;
- município;
- data e hora de saída;
- data e hora prevista de retorno;
- quantidade de pernoites;
- objetivo da viagem;
- anexos da solicitação, quando aplicável (PDF, PNG, JPG, JPEG, DOC ou DOCX).

O grupo funcional do servidor é obtido do cadastro do usuário. A data de saída não pode ser anterior à data atual, e o retorno deve ser posterior à saída.

## Localidades e distância

A versão demonstrativa usa uma lista reduzida de destinos em `static/localidades.js`. A distância rodoviária aproximada entre Lebon Régis/SC e cada destino é cadastrada internamente. O usuário não escolhe manualmente a faixa de distância; o sistema a identifica automaticamente.

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

O `app.py` lê as distâncias diretamente do objeto `distanciasLocalidadesKm` desse arquivo. Ao incluir novos destinos, mantenha o mesmo formato (chaves `"UF|Município"` entre aspas e valores numéricos).

## Valores-base das diárias

Valores estabelecidos pela Lei Municipal nº 1.839/2026 de Lebon Régis:

| Faixa | Prefeito, Vice-Prefeito, Vereadores e Secretários | Demais servidores |
|---|---:|---:|
| Até 200 km dentro de SC | R$ 300,00 | R$ 300,00 |
| Acima de 200 km dentro de SC | R$ 600,00 | R$ 500,00 |
| Fora de SC até 1.000 km ou Capital de SC | R$ 700,00 | R$ 800,00 |
| Acima de 1.000 km ou Capital Federal | R$ 1.500,00 | R$ 1.300,00 |

O grupo "Demais servidores" abrange servidores efetivos, contratados, temporários e ocupantes de cargos em comissão.

## Cálculo do período e das diárias

O sistema calcula a duração total do afastamento a partir da data e hora de saída até a data e hora de retorno.

A legislação de referência define as frações para um período simples, mas não detalha a decomposição de afastamentos com vários dias. Por isso, a versão demonstrativa adota uma regra operacional isolada no backend, que não deve ser apresentada como texto literal da legislação:

- cada bloco completo de 24 horas corresponde a 1,00 diária;
- o período residual com pernoite corresponde a 1,00 diária;
- o período residual superior a 12 horas sem pernoite corresponde a 0,70 diária;
- o período residual inferior a 12 horas sem pernoite corresponde a 0,50 diária;
- o período residual de exatamente 12 horas sem pernoite corresponde a 0,70 diária (decisão operacional, pois o caso não é definido expressamente na legislação).

O período residual é considerado com pernoite quando a quantidade de pernoites informada é maior que a quantidade de blocos completos de 24 horas. A quantidade máxima de pernoites corresponde ao número de dias entre as datas de saída e de retorno; viagens com saída e retorno no mesmo dia devem ter zero pernoites. O sistema não presume que a mudança de data significa pernoite.

Fórmula simplificada:

```text
distância + grupo funcional -> valor-base
duração + quantidade de pernoites -> quantidade de diárias
valor-base x quantidade de diárias -> valor total estimado
```

O valor exibido no formulário é uma prévia calculada no navegador (`static/calculo_diarias.js`). O valor definitivo é recalculado pelo backend (`app.py`) antes de ser salvo; por isso, as duas implementações devem ser mantidas iguais.

## Prestação de contas

Após a aprovação da viagem, o solicitante pode enviar a prestação de contas com resumo da viagem, horários, meio de transporte, valor a devolver, quando aplicável, e comprovantes de deslocamento e de cumprimento do objetivo. Cada tipo de comprovante exige de 1 a 10 arquivos em PDF, PNG, JPG ou JPEG. Quando o meio de transporte é veículo oficial, também são exigidos o KM de saída e o KM de chegada.

Quando o valor a devolver é igual ao valor recebido (devolução integral, ou seja, viagem não realizada), apenas o resumo é obrigatório; horários, meio de transporte e comprovantes deixam de ser exigidos.

O validador pode aprovar, aprovar com ressalvas, rejeitar ou solicitar correção da prestação, conforme o status atual do processo.

## Prazo da prestação de contas

Na versão demonstrativa, são consideradas pendentes as solicitações aprovadas cujo retorno ocorreu há pelo menos dois dias e que ainda não possuem prestação de contas, além das prestações com correção solicitada na mesma condição. A contagem considera a data de retorno, sem o horário. Essa regra simplifica o tratamento do prazo e não contempla integralmente a previsão da Lei Municipal nº 1.839/2026 quanto ao primeiro dia útil subsequente.

Enquanto a pendência permanecer, uma nova solicitação fica indisponível, mas o processo pendente continua acessível para sua regularização. O painel mantém o botão de nova solicitação visível, mas bloqueado, exibe o motivo da restrição e oferece link para abrir a solicitação pendente.

## Indicador visual do processo

A tela de detalhes da solicitação possui uma linha de progresso com as macroetapas do processo. Correções e rejeições continuam sendo controladas pelos status internos detalhados. Quando o status é `rejeitada`, o processo aparece como interrompido, sem marcar indevidamente a conclusão como finalizada.

## Recursos de apoio ao preenchimento

A interface indica os campos obrigatórios, aplica máscaras de preenchimento para CPF e horários e oferece a opção de alto contraste. Também utiliza ícones de informação com tooltips em campos que possuem regras ou conceitos menos óbvios, como distância, quantidade de pernoites, quantidade de diárias, valor-base e comprovantes.

## Página inicial

Visitantes não autenticados acessam uma página inicial de apresentação com o objetivo do sistema, o fluxo, os perfis, o aviso de ambiente demonstrativo e o acesso ao login.

## Isolamento do ambiente demonstrativo

Esta versão acadêmica cria um ambiente temporário isolado para cada sessão do navegador. No primeiro acesso, o servidor gera um identificador aleatório com `uuid.uuid4().hex`, copia o banco-modelo `diarias.db` para o diretório temporário do sistema operacional e passa a executar todas as consultas e alterações somente nessa cópia. Os uploads seguem o mesmo isolamento.

Estrutura de cada sessão:

```text
<diretório temporário>/diaria_digital_demo/<demo_environment_id>/
├── diarias.db
└── uploads/
```

Assim, solicitações, prestações de contas, aprovações, usuários e anexos criados por um visitante não aparecem para outro. O logout remove apenas a autenticação e preserva o ambiente, permitindo alternar entre os perfis solicitante e validador no mesmo fluxo. A ação **Reiniciar demonstração** remove somente a cópia e os uploads da sessão atual; o próximo acesso recebe um ambiente limpo.

O banco `diarias.db` incluído no projeto é um modelo inicial que não é alterado durante o uso normal. Cada nova cópia garante os três acessos demonstrativos, prepara dinamicamente a viagem vencida do CPF `111.111.111-11`, com retorno três dias antes da data atual, e mantém o CPF `333.333.333-33` sem pendência vencida inicial. Ambientes sem utilização há mais de 7 dias são removidos quando outro ambiente é criado.

A sessão do navegador permanece válida por até 7 dias. Assim, fechar e reabrir normalmente o mesmo navegador não reinicia a demonstração: enquanto o cookie e os arquivos temporários existirem, o mesmo ambiente será recuperado. **Reiniciar demonstração** continua sendo o mecanismo explícito para apagar os dados daquele ambiente e restaurar seu estado inicial.

Os dados são deliberadamente temporários. Os 7 dias representam a retenção da aplicação enquanto o armazenamento temporário continuar disponível; uma reinicialização da infraestrutura do Render pode eliminar esses arquivos antes desse prazo. Essa arquitetura existe para a avaliação acadêmica simultânea e não é uma recomendação de armazenamento para uso institucional em produção.

## Execução local

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Execute a aplicação:

```bash
python app.py
```

3. Acesse:

```text
http://127.0.0.1:5000
```

A execução por `python app.py` utiliza o servidor de desenvolvimento do Flask em modo de depuração e destina-se apenas ao uso local.

## Deploy

A aplicação também está hospedada no Render, onde é executada pelo `gunicorn`. Como o repositório não possui os arquivos `Procfile` ou `render.yaml`, o comando de inicialização (`gunicorn app:app`) foi configurado diretamente no painel do Render.

A chave de sessão (`SECRET_KEY`) definida em `app.py` é de uso exclusivamente acadêmico e deve ser substituída por um valor secreto em qualquer uso fora da demonstração. O repositório não contém tokens ou credenciais de acesso à hospedagem.

## Limitações

Uma eventual implantação na Administração Municipal exigiria adequações na infraestrutura, especialmente quanto ao armazenamento permanente dos dados e documentos, mecanismos de segurança, auditoria, cópias de segurança, proteção de dados pessoais, validações normativas completas e integração com os sistemas institucionais.
