# Sistema Web de Gestao de Diarias

Projeto academico simples para demonstrar o fluxo de gestao de diarias com dois perfis:

- Servidor solicitante: cadastra solicitacao, informa destino, datas, horarios, pernoite, objetivo, anexos e envia prestacao de contas.
- Servidor validador: cadastra usuarios, visualiza solicitacoes, confere o calculo automatico, aprova ou solicita correcao.
- Calculo automatico da diaria por grupo funcional, municipio de destino, distancia cadastrada, faixa legal, duracao prevista e fator de pernoite.


## Pagina inicial publica

Ao acessar `/` sem estar autenticado, o sistema exibe uma pagina inicial de apresentacao do Diaria Digital, com resumo do objetivo academico, fluxo principal, perfis de acesso e aviso de ambiente demonstrativo.

O botao `Acessar o sistema` direciona para `/login`. Usuarios autenticados continuam sendo redirecionados automaticamente pela rota `/` para o painel correspondente ao perfil: solicitante ou validador.

## Autenticacao por CPF

A versao demonstrativa usa CPF + senha para acesso. O CPF e armazenado internamente somente com numeros, sem pontos ou hifen, e a interface aplica mascara visual no formato `000.000.000-00`.

A validacao desta versao academica confere presenca e quantidade de 11 digitos apos a normalizacao. Nao ha validacao matematica dos digitos verificadores oficiais do CPF, pois os dados de demonstracao sao ficticios.

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

Fatores por duracao e pernoite:

- Superior a 12 horas com pernoite: fator 1,00.
- Superior a 12 horas sem pernoite: fator 0,70.
- Inferior a 12 horas sem pernoite: fator 0,50.

O valor definitivo e sempre recalculado no backend Flask antes de salvar.

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

- Solicitante: `111.111.111-11` / `123456`
- Validador: `222.222.222-22` / `123456`

## Observacoes de escopo

Este projeto e intencionalmente academico e local. Para uso real, seria necessario reforcar seguranca, auditoria, controle de permissoes em anexos, regras formais de valores e integracao com sistemas institucionais.

## Documentacao complementar

Consulte `DOCUMENTACAO.md` para uma explicacao sobre fluxos, regras de negocio, banco de dados e principais nomes tecnicos usados no codigo.
