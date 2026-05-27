# Sistema Web de Gestão de Diárias

Projeto acadêmico simples para demonstrar o fluxo de gestão de diárias com dois perfis:

- Servidor solicitante: cadastra solicitação, informa dados da viagem, anexa comprovantes e envia prestação de contas.
- Servidor validador: visualiza solicitações, aprova ou solicita correção.
- Cálculo de diária por enquadramento do cargo, faixa da viagem e existência de estadia.

## Tecnologias

- Python
- Flask
- SQLite

## Como executar

1. Crie e ative um ambiente virtual, se desejar.
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Execute o sistema:

```bash
python app.py
```

4. Acesse `http://127.0.0.1:5000`.

## Usuários de demonstração

- Solicitante: `solicitante@academico.test` / `123456`
- Validador: `validador@academico.test` / `123456`

## Observações de escopo

Este projeto é intencionalmente acadêmico e local. Para uso real, seria necessário reforçar segurança, auditoria, controle de permissões em anexos, regras formais de valores e integração com sistemas institucionais.

## Documentação complementar

Consulte `DOCUMENTACAO.md` para uma explicação em português sobre os fluxos, regras de negócio e principais nomes técnicos usados no código.
