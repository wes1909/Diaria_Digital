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

const campoGrupoDiaria = document.querySelector("#dailyGroupSelect");
const campoPernoite = document.querySelector("#overnightSelect");
const campoValorEstimadoVisual = document.querySelector("#estimatedAmountDisplay");
const campoValorEstimado = document.querySelector("#estimatedAmountInput");
const campoDataSaidaDiaria = document.querySelector("#departureDate");
const campoDataRetornoDiaria = document.querySelector("#returnDate");
const campoHoraSaida = document.querySelector("#departureTime");
const campoHoraRetorno = document.querySelector("#returnTime");
const resumoDestino = document.querySelector("#summaryDestination");
const resumoDistancia = document.querySelector("#summaryDistance");
const resumoDuracao = document.querySelector("#summaryDuration");
const resumoFaixa = document.querySelector("#summaryRange");
const resumoFator = document.querySelector("#summaryFactor");
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

function obterFator(duracaoHoras) {
    if (duracaoHoras === null) {
        return null;
    }
    const temPernoite = campoPernoite.value === "1";
    if (temPernoite) {
        return duracaoHoras > 12 ? 1.0 : null;
    }
    if (duracaoHoras > 12) {
        return 0.7;
    }
    if (duracaoHoras < 12) {
        return 0.5;
    }
    return null;
}

function atualizarTexto(campo, texto) {
    if (campo) {
        campo.textContent = texto;
    }
}

function atualizarValorDiaria() {
    const grupo = valoresDiarias[campoGrupoDiaria?.value];
    const localidade = window.obterLocalidadeSelecionada?.() || null;
    const faixaCodigo = obterFaixa(localidade);
    const faixa = grupo?.ranges[faixaCodigo];
    const duracaoHoras = obterDuracaoHoras();
    const fator = obterFator(duracaoHoras);
    const valorTotal = faixa && fator !== null ? faixa.amount * fator : 0;

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
    atualizarTexto(resumoFaixa, faixa ? faixa.label : "Aguardando distância cadastrada");
    atualizarTexto(resumoFator, fator !== null ? formatarNumero(fator, 2) : "-");
    atualizarTexto(resumoValorBase, faixa ? formatarMoeda(faixa.amount) : "-");
    atualizarTexto(resumoValorTotal, formatarMoeda(valorTotal));
}

if (campoGrupoDiaria && campoPernoite && campoValorEstimadoVisual && campoValorEstimado) {
    atualizarValorDiaria();
    document.addEventListener("localidade:alterada", atualizarValorDiaria);
    campoPernoite.addEventListener("change", atualizarValorDiaria);
    campoDataSaidaDiaria?.addEventListener("change", atualizarValorDiaria);
    campoDataRetornoDiaria?.addEventListener("change", atualizarValorDiaria);
    campoHoraSaida?.addEventListener("change", atualizarValorDiaria);
    campoHoraRetorno?.addEventListener("change", atualizarValorDiaria);
}
