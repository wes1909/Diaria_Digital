# Diaria Digital

Diaria Digital e um sistema web academico desenvolvido para demonstrar a digitalizacao do processo de solicitacao, analise, aprovacao, viagem e prestacao de contas de diarias na Administracao Publica Municipal.

O projeto e um ambiente demonstrativo. Ele nao representa um sistema oficialmente implantado em producao institucional, e os dados usados devem ser ficticios.

## Tecnologias

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript
- Gunicorn

O projeto possui `requirements.txt` com as dependencias Python. Nao ha arquivo de configuracao de deploy com credenciais no repositorio.

## Perfis de acesso

- **Servidor Solicitante**: cria solicitacoes de diaria, acompanha o andamento, corrige solicitacoes quando necessario e envia a prestacao de contas.
- **Servidor Validador**: cadastra usuarios, analisa solicitacoes, aprova, rejeita, solicita correcoes e avalia prestacoes de contas.

## Usuarios demonstrativos

- **Solicitante com pendencia**: CPF `111.111.111-11`, senha `123456`.
  Demonstra o bloqueio por prestacao de contas vencida.
- **Validador**: CPF `222.222.222-22`, senha `123456`.
  Demonstra o painel de analise, validacao e cadastro de usuarios.
- **Solicitante sem pendencia**: CPF `333.333.333-33`, senha `123456`.
  Demonstra o fluxo normal de uma nova solicitacao.

## Autenticacao

O acesso ao sistema e feito por CPF + senha. O CPF e usado como identificador de acesso, armazenado internamente apenas com numeros, e exibido na interface com mascara `000.000.000-00`.

Os CPFs demonstrativos sao ficticios. Nao utilize CPF real, dados bancarios reais ou documentos pessoais reais neste ambiente.

## Fluxo principal

O sistema apresenta uma linha visual de progresso com cinco macroetapas:

```text
Solicitacao -> Analise -> Viagem -> Prestacao de contas -> Conclusao
```

Essa linha e apenas uma representacao visual simplificada. Os status internos continuam sendo mais detalhados e controlam as permissoes, transicoes, correcoes, aprovacoes e rejeicoes.

## Solicitacao de diaria

O solicitante informa:

- estado;
- municipio;
- data e hora de saida;
- data e hora prevista de retorno;
- quantidade de pernoites;
- objetivo da viagem;
- anexos da solicitacao, quando aplicavel.

O grupo funcional do servidor e obtido do cadastro do usuario.

## Localidades e distancia

A versao demonstrativa usa uma lista reduzida de destinos em `static/localidades.js`. A distancia rodoviaria aproximada entre Lebon Regis/SC e cada destino e cadastrada internamente. O usuario nao escolhe manualmente a faixa de distancia; o sistema identifica a faixa automaticamente.

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

## Valores-base das diarias

| Faixa | Prefeito/Vice/Vereadores/Secretarios | Demais servidores |
|---|---:|---:|
| Ate 200 km dentro de SC | R$ 300,00 | R$ 300,00 |
| Acima de 200 km dentro de SC | R$ 600,00 | R$ 500,00 |
| Fora de SC ate 1.000 km ou Capital de SC | R$ 700,00 | R$ 800,00 |
| Acima de 1.000 km ou Capital Federal | R$ 1.500,00 | R$ 1.300,00 |

## Calculo do periodo e das diarias

O sistema calcula a duracao total do afastamento combinando data/hora de saida ate data/hora de retorno.

Para a versao demonstrativa, afastamentos superiores a 24 horas sao tratados por uma regra operacional isolada no backend. Essa regra decompoe o periodo em blocos completos de 24 horas e eventual periodo residual. Ela nao deve ser apresentada como texto literal da legislacao.

- Cada bloco completo de 24 horas corresponde a 1,00 diaria.
- O periodo residual e analisado conforme duracao e pernoites informados.
- A quantidade total de diarias e multiplicada pelo valor-base.
- O campo antigo "Havera pernoite?" foi substituido por "Quantidade de pernoites".
- O sistema nao presume automaticamente que a mudanca de data significa pernoite.

Formula simplificada:

```text
distancia + grupo funcional -> valor-base
duracao + quantidade de pernoites -> quantidade de diarias
valor-base * quantidade de diarias -> valor total estimado
```

## Prestacao de contas

Apos a aprovacao da viagem, o solicitante pode enviar a prestacao de contas com resumo da viagem, horarios, meio de transporte, valor a devolver quando aplicavel e comprovantes de deslocamento e de cumprimento do objetivo.

O validador pode aprovar, aprovar com ressalvas, rejeitar ou solicitar correcao da prestacao, conforme o status atual do processo.

## Regra das 48 horas

O sistema identifica prestacao de contas pendente apos o prazo configurado de 48 horas do retorno. Enquanto houver pendencia vencida, o solicitante nao pode criar nova solicitacao. O painel mantem o botao de nova solicitacao visivel, mas bloqueado, exibe o motivo da restricao e oferece link para abrir a solicitacao pendente.

## Indicador visual do processo

A tela de detalhes da solicitacao possui uma linha de progresso com as macroetapas do processo. Correcoes e rejeicoes continuam sendo controladas pelos status internos detalhados. Quando o status e `rejeitada`, o processo aparece como interrompido, sem marcar indevidamente a conclusao como finalizada.

## Tooltips

A interface usa icones de informacao com tooltips em campos que possuem regras ou conceitos menos obvios, como distancia, quantidade de pernoites, quantidade de diarias, valor-base e comprovantes.

## Pagina inicial

Visitantes nao autenticados acessam uma pagina inicial de apresentacao com objetivo do sistema, fluxo, perfis, aviso de ambiente demonstrativo e acesso ao login.

## Execucao local

1. Instale as dependencias:

```bash
pip install -r requirements.txt
```

2. Execute a aplicacao:

```bash
python app.py
```

3. Acesse:

```text
http://127.0.0.1:5000
```

## Deploy

A aplicacao possui dependencia `gunicorn`, utilizada em ambientes de hospedagem como Render. Nao ha credenciais, tokens ou configuracoes sensiveis documentadas no repositorio.

## Limitacoes

Para uso real, ainda seriam necessarios aprimoramentos de seguranca, auditoria, protecao de dados pessoais, armazenamento adequado de arquivos, integracao com sistemas institucionais, validacoes normativas completas e infraestrutura de producao.
