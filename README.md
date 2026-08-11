# Sistema Web de Gestao de Diarias

Projeto academico simples para demonstrar o fluxo de gestao de diarias com dois perfis:

- Servidor solicitante: cadastra solicitacao, informa destino, datas, horarios, quantidade de pernoites, objetivo, anexos e envia prestacao de contas.
- Servidor validador: cadastra usuarios, visualiza solicitacoes, confere o calculo automatico, aprova ou solicita correcao.
- Calculo automatico da diaria por grupo funcional, municipio de destino, distancia cadastrada, faixa legal, duracao total prevista e quantidade de pernoites.


## Pagina inicial publica

Ao acessar `/` sem estar autenticado, o sistema exibe uma pagina inicial de apresentacao do Diaria Digital, com resumo do objetivo academico, fluxo principal, perfis de acesso e aviso de ambiente demonstrativo.

O botao `Acessar o sistema` direciona para `/login`. Usuarios autenticados continuam sendo redirecionados automaticamente pela rota `/` para o painel correspondente ao perfil: solicitante ou validador.

## Autenticacao por CPF

A versao demonstrativa usa CPF + senha para acesso. O CPF e armazenado internamente somente com numeros, sem pontos ou hifen, e a interface aplica mascara visual no formato `000.000.000-00`.

O backend sempre normaliza o CPF recebido antes de consultar ou salvar. A validacao desta versao academica confere presenca e quantidade de 11 digitos apos a normalizacao. Nao ha validacao matematica dos digitos verificadores oficiais do CPF, pois os dados de demonstracao sao ficticios.

A coluna antiga `email` pode permanecer no SQLite apenas como legado tecnico da estrutura original. Ela nao e usada para login, cadastro, pesquisa ou exibicao na interface. Novos usuarios recebem um valor tecnico interno nessa coluna apenas para compatibilidade com a restricao antiga do banco.

A mascara visual fica em `static/cpf.js` e e usada no login e no formulario de cadastro/edicao de servidores.

## Regras atuais de calculo

Grupos funcionais:

- `agente_politico_comissionado`: Prefeito Municipal, Vice-Prefeito, Vereadores e Secretarios.
- `servidor_geral`: demais servidores publicos efetivos, contratados, temporarios e ocupantes de cargos em comissao.

Valores-base:

| Faixa | Prefeito/Vice/Vereadores/Secretarios | Demais servidores |
|---|---:|---:|
| Ate 200 km dentro de SC | R$ 300,00 | R$ 300,00 |
| Acima de 200 km dentro de SC | R$ 600,00 | R$ 500,00 |
| Fora de SC ate 1.000 km ou Capital de SC | R$ 700,00 | R$ 800,00 |
| Acima de 1.000 km ou Capital Federal | R$ 1.500,00 | R$ 1.300,00 |

Quantidade de diarias por duracao e pernoites:

O formulario utiliza o campo `Quantidade de pernoites`, com valor inteiro maior ou igual a zero. O backend valida esse numero, limita ao maximo possivel entre a data de saida e a data de retorno e impede pernoite em viagens com saida e retorno no mesmo dia.

A quantidade total de diarias fica em `daily_quantity` e e calculada pela funcao `calculate_daily_quantity()`:

- Cada bloco completo de 24 horas corresponde a 1,00 diaria.
- O periodo residual e calculado pela regra operacional demonstrativa.
- Residual superior a 12 horas com pernoite associado: 1,00 diaria.
- Residual superior a 12 horas sem pernoite associado: 0,70 diaria.
- Residual inferior a 12 horas sem pernoite associado: 0,50 diaria.
- Blocos completos de 24 horas consomem, no maximo, um pernoite cada. Se os pernoites informados excederem os blocos completos, o residual e considerado com pernoite.

Exemplos:

| Duracao total | Pernoites | Quantidade calculada |
|---:|---:|---:|
| 10 horas | 0 | 0,50 diaria |
| 14 horas | 0 | 0,70 diaria |
| 14 horas | 1 | 1,00 diaria |
| 30 horas | 1 | 1,50 diaria |
| 48 horas | 2 | 2,00 diarias |
| 62 horas | 2 | 2,70 diarias |
| 62 horas | 3 | 3,00 diarias |

A versao demonstrativa utiliza uma regra operacional para decompor afastamentos superiores a 24 horas em blocos completos e periodo residual. Essa logica foi isolada para permitir adequacao futura caso exista regulamentacao administrativa especifica sobre a forma de calculo de multiplas diarias. Essa decomposicao nao deve ser apresentada como texto literal da Lei Municipal n. 1.839/2026.

Para periodo exatamente igual a 12 horas, o sistema adota a decisao operacional demonstrativa de aplicar 0,70 diaria quando nao houver pernoite associado ao periodo residual. O valor definitivo e sempre recalculado no backend Flask antes de salvar.

O valor total estimado e calculado como:

```text
valor total = valor-base da diaria * daily_quantity
```

No calculo atual, novas solicitacoes gravam:

- `overnight_count`: quantidade de pernoites informada e validada.
- `daily_quantity`: quantidade total de diarias calculada.

Os campos antigos `has_overnight` e `daily_factor` podem permanecer no banco como legado/fallback para registros anteriores.

## Municipios e distancias

A lista de destinos fica em `static/localidades.js`, na estrutura `localidadesNomesBrasil`. Para o modo de demonstracao academica, a base foi reduzida para 15 destinos:

| UF | Municipio | Distancia rodoviaria aproximada |
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

As distancias ficam no objeto `distanciasLocalidadesKm`, usando chaves no formato `UF|Municipio`. Os valores sao numericos e representam quilometros inteiros aproximados, sem a unidade `km` no codigo.

Exemplo:

```js
const distanciasLocalidadesKm = {
    "SC|Lebon Regis": 0,
    "SC|Cacador": 50
};
```

As distancias devem ser rodoviarias, considerando deslocamento por vias terrestres entre Lebon Regis/SC e a sede do municipio de destino. Nao use distancia em linha reta, formula de Haversine ou estimativas baseadas apenas em latitude e longitude.

Rio de Janeiro/RJ foi cadastrado com 1.102 km para demonstrar destino comum acima de 1.000 km, com base em distancia rodoviaria aproximada consultada em RotaMapas e conferida com valor semelhante no Rome2Rio.

## Banco de dados demonstrativo

O banco SQLite `diarias.db` mantem a estrutura das tabelas principais do sistema:

- `users`
- `requests`
- `attachments`

Para a demonstracao atual, os registros antigos de teste foram removidos e a base foi reiniciada com apenas os dois usuarios demonstrativos padrao. As tabelas e colunas usadas pelo fluxo de solicitacao, aprovacao, anexos e prestacao de contas foram preservadas.

A tabela `users` possui a coluna `cpf`, usada como identificador funcional de login. O sistema tambem cria um indice unico para CPF quando possivel, evitando duplicidade de usuarios com o mesmo documento.

## Tecnologias

- Python
- Flask
- SQLite

## Como executar

1. Crie e ative um ambiente virtual, se desejar.
2. Instale as dependencias:

```bash
pip install -r requirements.txt
```

3. Execute o sistema:

```bash
python app.py
```

4. Acesse `http://127.0.0.1:5000`.

## Usuarios de demonstracao

- Servidor Solicitante: CPF `111.111.111-11`, senha `123456`
- Servidor Validador: CPF `222.222.222-22`, senha `123456`

O CPF tambem pode ser digitado sem pontuacao, por exemplo `11111111111`.

## Observacoes de escopo

Este projeto e intencionalmente academico e local. Para uso real, seria necessario reforcar seguranca, auditoria, controle de permissoes em anexos, regras formais de valores e integracao com sistemas institucionais.

## Documentacao complementar

Consulte `DOCUMENTACAO.md` para uma explicacao sobre fluxos, regras de negocio, banco de dados e principais nomes tecnicos usados no codigo.
