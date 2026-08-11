const valoresDiarias = {
    agente_politico_comissionado: {
        label: "Prefeito Municipal, Vice-Prefeito, Vereadores e Secretários",
        ranges: {
            sc_ate_200: { label: "Até 200 km dentro de Santa Catarina", amount: 300.00 },
            sc_acima_200: { label: "Acima de 200 km dentro de Santa Catarina", amount: 600.00 },
            capital_sc_ou_fora_ate_1000: { label: "Capital de SC ou fora do Estado até 1000 km", amount: 700.00 },
            capital_federal_ou_acima_1000: { label: "Capital Federal ou acima de 1000 km", amount: 1500.00 },
        },
    },
    servidor_geral: {
        label: "Demais servidores efetivos, contratados, temporários e cargos em comissão",
        ranges: {
            sc_ate_200: { label: "Até 200 km dentro de Santa Catarina", amount: 300.00 },
            sc_acima_200: { label: "Acima de 200 km dentro de Santa Catarina", amount: 500.00 },
            capital_sc_ou_fora_ate_1000: { label: "Capital de SC ou fora do Estado até 1000 km", amount: 800.00 },
            capital_federal_ou_acima_1000: { label: "Capital Federal ou acima de 1000 km", amount: 1300.00 },
        },
    },
};

const FRACAO_OPERACIONAL_12_HORAS = 0.70;

const campoGrupoDiaria = document.querySelector("#dailyGroupSelect");
const campoPernoites = document.querySelector("#overnightCount");
const avisoLimitePernoites = document.querySelector("#overnightLimitHint");
const campoValorEstimadoVisual = document.querySelector("#estimatedAmountDisplay");
const campoValorEstimado = document.querySelector("#estimatedAmountInput");
const campoDataSaidaDiaria = document.querySelector("#departureDate");
const campoDataRetornoDiaria = document.querySelector("#returnDate");
const campoHoraSaida = document.querySelector("#departureTime");
const campoHoraRetorno = document.querySelector("#returnTime");
const resumoDestino = document.querySelector("#summaryDestination");
const resumoDistancia = document.querySelector("#summaryDistance");
const resumoDuracao = document.querySelector("#summaryDuration");
const resumoPernoites = document.querySelector("#summaryOvernightCount");
const resumoFaixa = document.querySelector("#summaryRange");
const resumoQuantidadeDiarias = document.querySelector("#summaryDailyQuantity");
const resumoValorBase = document.querySelector("#summaryBaseAmount");
const resumoValorTotal = document.querySelector("#summaryTotalAmount");

function formatarMoeda(valor) {
    return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatarNumero(valor, casas = 1) {
    return Number(valor).toLocaleString("pt-BR", {
        minimumFractionDigits: casas,
        maximumFractionDigits: casas,
    });
}

function formatarQuantidadeDiarias(valor) {
    const texto = formatarNumero(valor, 2);
    return `${texto} ${Math.abs(valor - 1) < 0.001 ? "diária" : "diárias"}`;
}

function obterDatasViagem() {
    if (!campoDataSaidaDiaria?.value || !campoDataRetornoDiaria?.value) {
        return null;
    }
    const saida = new Date(`${campoDataSaidaDiaria.value}T00:00`);
    const retorno = new Date(`${campoDataRetornoDiaria.value}T00:00`);
    if (Number.isNaN(saida.getTime()) || Number.isNaN(retorno.getTime()) || retorno < saida) {
        return null;
    }
    return { saida, retorno };
}

function obterMaximoPernoites() {
    const datas = obterDatasViagem();
    if (!datas) {
        return null;
    }
    return Math.max(Math.round((datas.retorno.getTime() - datas.saida.getTime()) / 86400000), 0);
}

function obterDuracaoHoras() {
    if (!campoDataSaidaDiaria?.value || !campoDataRetornoDiaria?.value || !campoHoraSaida?.value || !campoHoraRetorno?.value) {
        return null;
    }
    const saida = new Date(`${campoDataSaidaDiaria.value}T${campoHoraSaida.value}`);
    const retorno = new Date(`${campoDataRetornoDiaria.value}T${campoHoraRetorno.value}`);
    if (Number.isNaN(saida.getTime()) || Number.isNaN(retorno.getTime()) || retorno <= saida) {
        return null;
    }
    return (retorno.getTime() - saida.getTime()) / 3600000;
}

function obterDistanciaKm(localidade) {
    if (!localidade) {
        return null;
    }
    return localidade.distancia_km ?? localidade.distanciaKm ?? null;
}

function obterFaixa(localidade) {
    if (!localidade) {
        return null;
    }
    const distanciaKm = obterDistanciaKm(localidade);
    if (localidade.capitalFederal) {
        return "capital_federal_ou_acima_1000";
    }
    if (localidade.capitalEstadual) {
        return "capital_sc_ou_fora_ate_1000";
    }
    if (distanciaKm === null || distanciaKm === undefined || distanciaKm === "") {
        return null;
    }
    if (distanciaKm > 1000) {
        return "capital_federal_ou_acima_1000";
    }
    if (localidade.uf === "SC") {
        return distanciaKm <= 200 ? "sc_ate_200" : "sc_acima_200";
    }
    return "capital_sc_ou_fora_ate_1000";
}

function obterQuantidadePernoites() {
    const valor = campoPernoites?.value || "0";
    if (!/^\d+$/.test(valor)) {
        return null;
    }
    return Number.parseInt(valor, 10);
}

function calcularFracaoResidual(horasResiduais, residualComPernoite) {
    if (horasResiduais <= 0) {
        return 0;
    }
    if (residualComPernoite) {
        return 1;
    }
    if (horasResiduais > 12) {
        return 0.70;
    }
    if (horasResiduais < 12) {
        return 0.50;
    }
    return FRACAO_OPERACIONAL_12_HORAS;
}

function obterQuantidadeDiarias(duracaoHoras, pernoites) {
    if (duracaoHoras === null || pernoites === null) {
        return null;
    }
    const blocos24h = Math.floor(duracaoHoras / 24);
    const horasResiduais = duracaoHoras - (blocos24h * 24);
    const residualComPernoite = pernoites > blocos24h;
    return blocos24h + calcularFracaoResidual(horasResiduais, residualComPernoite);
}

function atualizarTexto(campo, texto) {
    if (campo) {
        campo.textContent = texto;
    }
}

function atualizarLimitePernoites() {
    const maximo = obterMaximoPernoites();
    if (maximo === null) {
        if (avisoLimitePernoites) {
            avisoLimitePernoites.textContent = "Máximo possível para este período: -";
        }
        return;
    }

    if (campoPernoites) {
        campoPernoites.max = String(maximo);
        const valorAtual = obterQuantidadePernoites();
        if (valorAtual !== null && valorAtual > maximo) {
            campoPernoites.value = String(maximo);
        }
    }
    if (avisoLimitePernoites) {
        avisoLimitePernoites.textContent = `Máximo possível para este período: ${maximo} ${maximo === 1 ? "pernoite" : "pernoites"}`;
    }
}

function atualizarValorDiaria() {
    atualizarLimitePernoites();

    const grupo = valoresDiarias[campoGrupoDiaria?.value];
    const localidade = window.obterLocalidadeSelecionada?.() || null;
    const faixaCodigo = obterFaixa(localidade);
    const faixa = grupo?.ranges[faixaCodigo];
    const duracaoHoras = obterDuracaoHoras();
    const pernoites = obterQuantidadePernoites();
    const quantidadeDiarias = obterQuantidadeDiarias(duracaoHoras, pernoites);
    const valorTotal = faixa && quantidadeDiarias !== null ? faixa.amount * quantidadeDiarias : 0;

    campoValorEstimadoVisual.value = formatarMoeda(valorTotal);
    campoValorEstimado.value = valorTotal.toFixed(2);

    atualizarTexto(resumoDestino, localidade ? `${localidade.nome} - ${localidade.uf}` : "-");
    atualizarTexto(
        resumoDistancia,
        localidade?.distanciaKm !== null && localidade?.distanciaKm !== undefined
            ? `${formatarNumero(localidade.distanciaKm, 0)} km`
            : "não cadastrada"
    );
    atualizarTexto(resumoDuracao, duracaoHoras !== null ? `${formatarNumero(duracaoHoras)} horas` : "-");
    atualizarTexto(resumoPernoites, pernoites !== null ? String(pernoites) : "-");
    atualizarTexto(resumoFaixa, faixa ? faixa.label : "Aguardando distância cadastrada");
    atualizarTexto(resumoQuantidadeDiarias, quantidadeDiarias !== null ? formatarQuantidadeDiarias(quantidadeDiarias) : "-");
    atualizarTexto(resumoValorBase, faixa ? formatarMoeda(faixa.amount) : "-");
    atualizarTexto(resumoValorTotal, formatarMoeda(valorTotal));
}

if (campoGrupoDiaria && campoPernoites && campoValorEstimadoVisual && campoValorEstimado) {
    atualizarValorDiaria();
    document.addEventListener("localidade:alterada", atualizarValorDiaria);
    campoPernoites.addEventListener("input", atualizarValorDiaria);
    campoPernoites.addEventListener("change", atualizarValorDiaria);
    campoDataSaidaDiaria?.addEventListener("change", atualizarValorDiaria);
    campoDataRetornoDiaria?.addEventListener("change", atualizarValorDiaria);
    campoHoraSaida?.addEventListener("change", atualizarValorDiaria);
    campoHoraRetorno?.addEventListener("change", atualizarValorDiaria);
}
