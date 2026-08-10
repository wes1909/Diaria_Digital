const campoMeioTransporte = document.querySelector("#transportMode");
const camposVeiculoOficial = document.querySelectorAll(".official-vehicle-field");
const campoKmSaida = document.querySelector("#departureKm");
const campoKmChegada = document.querySelector("#arrivalKm");
const camposKm = document.querySelectorAll(".km-input");
const campoValorDevolverVisual = document.querySelector("#refundAmountDisplay");
const campoValorDevolver = document.querySelector("#refundAmountInput");
const opcionaisNaDevolucaoIntegral = document.querySelectorAll(".optional-when-full-refund");

function atualizarCamposVeiculoOficial() {
    const veiculoOficialSelecionado = campoMeioTransporte?.value === "Veículo oficial";

    camposVeiculoOficial.forEach((campo) => {
        campo.hidden = !veiculoOficialSelecionado;
    });

    if (campoKmSaida && campoKmChegada) {
        campoKmSaida.required = veiculoOficialSelecionado;
        campoKmChegada.required = veiculoOficialSelecionado;
        campoKmSaida.disabled = !veiculoOficialSelecionado;
        campoKmChegada.disabled = !veiculoOficialSelecionado;
        if (!veiculoOficialSelecionado) {
            campoKmSaida.value = "";
            campoKmChegada.value = "";
        }
    }
}

if (campoMeioTransporte) {
    atualizarCamposVeiculoOficial();
    campoMeioTransporte.addEventListener("change", atualizarCamposVeiculoOficial);
}

camposKm.forEach((campo) => {
    campo.addEventListener("input", () => {
        campo.value = campo.value
            .replace(",", ".")
            .replace(/[^\d.]/g, "")
            .replace(/(\..*)\./g, "$1");
    });
});

function formatarDinheiro(valor) {
    return valor.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
    });
}

function atualizarValorDevolver() {
    if (!campoValorDevolverVisual || !campoValorDevolver) {
        return;
    }

    const centavos = campoValorDevolverVisual.value.replace(/\D/g, "");
    const valor = Number(centavos || "0") / 100;
    const valorMaximo = Number(campoValorDevolver.dataset.max || "0");
    const valorSeguro = Math.min(valor, valorMaximo);

    campoValorDevolverVisual.value = formatarDinheiro(valorSeguro);
    campoValorDevolver.value = valorSeguro.toFixed(2);
    atualizarModoDevolucaoIntegral();
}

if (campoValorDevolverVisual && campoValorDevolver) {
    atualizarModoDevolucaoIntegral();
    campoValorDevolverVisual.addEventListener("input", atualizarValorDevolver);
    campoValorDevolverVisual.addEventListener("blur", atualizarValorDevolver);
}

function atualizarModoDevolucaoIntegral() {
    if (!campoValorDevolver) {
        return;
    }

    const valor = Number(campoValorDevolver.value || "0");
    const valorMaximo = Number(campoValorDevolver.dataset.max || "0");
    const devolucaoIntegral = valorMaximo > 0 && valor === valorMaximo;

    opcionaisNaDevolucaoIntegral.forEach((elemento) => {
        elemento.classList.toggle("muted-block", devolucaoIntegral);
        elemento.querySelectorAll("input, select, textarea").forEach((campo) => {
            if (campo.dataset.originalRequired === undefined) {
                campo.dataset.originalRequired = campo.required ? "1" : "0";
            }
            campo.required = devolucaoIntegral ? false : campo.dataset.originalRequired === "1";
        });
    });

    if (devolucaoIntegral && campoMeioTransporte) {
        campoMeioTransporte.value = "";
        atualizarCamposVeiculoOficial();
    }
}
