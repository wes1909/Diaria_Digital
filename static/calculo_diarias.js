const valoresDiarias = {
    agente_politico_comissionado: {
        label: "Prefeito, Vice-Prefeito, Vereadores, Secretários e Cargos Comissionados",
        ranges: {
            sc_ate_200: {
                label: "Até 200 km dentro de Santa Catarina",
                amount: 300.00,
            },
            sc_acima_200: {
                label: "Acima de 200 km dentro de Santa Catarina",
                amount: 400.00,
            },
            capital_sc_ou_fora_ate_1000: {
                label: "Capital de SC ou fora do Estado até 1000 km",
                amount: 500.00,
            },
            capital_federal_ou_acima_1000: {
                label: "Capital Federal ou acima de 1000 km",
                amount: 1300.00,
            },
        },
    },
    servidor_geral: {
        label: "Demais servidores efetivos, contratados ou temporários",
        ranges: {
            sc_ate_200: {
                label: "Até 200 km dentro de Santa Catarina",
                amount: 205.00,
            },
            sc_acima_200: {
                label: "Acima de 200 km dentro de Santa Catarina",
                amount: 237.00,
            },
            acima_1000: {
                label: "Acima de 1000 km",
                amount: 809.00,
            },
        },
    },
};

const campoGrupoDiaria = document.querySelector("#dailyGroupSelect");
const campoFaixaDiaria = document.querySelector("#dailyRangeSelect");
const campoEstadia = document.querySelector("#overnightSelect");
const campoValorEstimadoVisual = document.querySelector("#estimatedAmountDisplay");
const campoValorEstimado = document.querySelector("#estimatedAmountInput");
const campoDataSaidaDiaria = document.querySelector("#departureDate");
const campoDataRetornoDiaria = document.querySelector("#returnDate");

function formatarMoeda(valor) {
    return valor.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
    });
}

function atualizarFaixasDiaria() {
    const grupo = valoresDiarias[campoGrupoDiaria.value];
    campoFaixaDiaria.innerHTML = "";

    if (!grupo) {
        campoFaixaDiaria.disabled = true;
        campoFaixaDiaria.append(new Option("Grupo do usuário não cadastrado", ""));
        atualizarValorDiaria();
        return;
    }

    campoFaixaDiaria.disabled = false;
    campoFaixaDiaria.append(new Option("Selecione o enquadramento", ""));

    Object.entries(grupo.ranges).forEach(([valor, faixa]) => {
        campoFaixaDiaria.append(new Option(faixa.label, valor));
    });

    if (campoFaixaDiaria.dataset.initialValue) {
        campoFaixaDiaria.value = campoFaixaDiaria.dataset.initialValue;
        delete campoFaixaDiaria.dataset.initialValue;
    }

    atualizarValorDiaria();
}

function atualizarValorDiaria() {
    const grupo = valoresDiarias[campoGrupoDiaria.value];
    const faixa = grupo?.ranges[campoFaixaDiaria.value];

    if (!faixa) {
        campoValorEstimadoVisual.value = "R$ 0,00";
        campoValorEstimado.value = "0";
        return;
    }

    const diasViagem = calcularDiasViagem();
    const valorUnitario = campoEstadia.value === "1" ? faixa.amount : faixa.amount / 2;
    const valorTotal = valorUnitario * diasViagem;
    campoValorEstimadoVisual.value = formatarMoeda(valorTotal);
    campoValorEstimado.value = valorTotal.toFixed(2);
}

function calcularDiasViagem() {
    if (!campoDataSaidaDiaria?.value || !campoDataRetornoDiaria?.value) {
        return 1;
    }

    const dataSaida = new Date(`${campoDataSaidaDiaria.value}T00:00:00`);
    const dataRetorno = new Date(`${campoDataRetornoDiaria.value}T00:00:00`);

    if (Number.isNaN(dataSaida.getTime()) || Number.isNaN(dataRetorno.getTime())) {
        return 1;
    }

    const diferencaMs = dataRetorno.getTime() - dataSaida.getTime();
    const diferencaDias = Math.floor(diferencaMs / 86400000) + 1;
    return Math.max(diferencaDias, 1);
}

if (
    campoGrupoDiaria &&
    campoFaixaDiaria &&
    campoEstadia &&
    campoValorEstimadoVisual &&
    campoValorEstimado
) {
    atualizarFaixasDiaria();
    campoFaixaDiaria.addEventListener("change", atualizarValorDiaria);
    campoEstadia.addEventListener("change", atualizarValorDiaria);
    campoDataSaidaDiaria?.addEventListener("change", atualizarValorDiaria);
    campoDataRetornoDiaria?.addEventListener("change", atualizarValorDiaria);
}
