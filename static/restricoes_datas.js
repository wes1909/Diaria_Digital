const campoDataSaida = document.querySelector("#departureDate");
const campoDataRetorno = document.querySelector("#returnDate");
const campoDataSaidaVisual = document.querySelector("#departureDateDisplay");
const campoDataRetornoVisual = document.querySelector("#returnDateDisplay");

function dataAtualISO() {
    const hoje = new Date();
    const deslocamento = hoje.getTimezoneOffset();
    const hojeLocal = new Date(hoje.getTime() - deslocamento * 60 * 1000);
    return hojeLocal.toISOString().slice(0, 10);
}

function formatarDataBR(valor) {
    if (!valor) {
        return "";
    }
    const [ano, mes, dia] = valor.split("-");
    return `${dia}/${mes}/${ano}`;
}

function atualizarDatasVisuais() {
    if (campoDataSaidaVisual) {
        const dataSaida = formatarDataBR(campoDataSaida.value);
        campoDataSaidaVisual.value = dataSaida;
        campoDataSaidaVisual.setAttribute(
            "aria-label",
            dataSaida ? `Data de saída selecionada: ${dataSaida}` : "Abrir calendário da data de saída"
        );
    }
    if (campoDataRetornoVisual) {
        const dataRetorno = formatarDataBR(campoDataRetorno.value);
        campoDataRetornoVisual.value = dataRetorno;
        campoDataRetornoVisual.setAttribute(
            "aria-label",
            dataRetorno ? `Data de retorno selecionada: ${dataRetorno}` : "Abrir calendário da data de retorno"
        );
    }
}

function notificarMudancaData(campo) {
    campo.dispatchEvent(new Event("change", { bubbles: true }));
}

function abrirCalendario(campo) {
    if (typeof campo.showPicker === "function") {
        campo.showPicker();
        return;
    }
    campo.focus();
}

function vincularCampoVisualAoCalendario(campoVisual, campoReal) {
    if (!campoVisual || !campoReal) {
        return;
    }

    campoVisual.addEventListener("click", () => abrirCalendario(campoReal));
    campoVisual.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter" || evento.key === " ") {
            evento.preventDefault();
            abrirCalendario(campoReal);
        }
    });
}

function atualizarLimitesDatas() {
    if (!campoDataSaida || !campoDataRetorno) {
        return;
    }

    const hoje = dataAtualISO();
    campoDataSaida.min = hoje;

    if (campoDataSaida.value) {
        campoDataRetorno.min = campoDataSaida.value;
    } else {
        campoDataRetorno.min = hoje;
    }

    if (campoDataSaida.value && campoDataSaida.value < hoje) {
        campoDataSaida.value = hoje;
    }

    if (
        campoDataSaida.value &&
        campoDataRetorno.value &&
        campoDataRetorno.value < campoDataSaida.value
    ) {
        campoDataRetorno.value = campoDataSaida.value;
        notificarMudancaData(campoDataRetorno);
    }

    atualizarDatasVisuais();
}

if (campoDataSaida && campoDataRetorno) {
    atualizarLimitesDatas();
    vincularCampoVisualAoCalendario(campoDataSaidaVisual, campoDataSaida);
    vincularCampoVisualAoCalendario(campoDataRetornoVisual, campoDataRetorno);
    campoDataSaida.addEventListener("change", atualizarLimitesDatas);
    campoDataRetorno.addEventListener("change", atualizarLimitesDatas);
}
