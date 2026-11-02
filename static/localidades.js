const localidadesNomesBrasil = {
    SC: [
        "Lebon R\u00e9gis",
        "Ca\u00e7ador",
        "Fraiburgo",
        "Curitibanos",
        "Campos Novos",
        "Lages",
        "Chapec\u00f3",
        "Joinville",
        "Blumenau",
        "Florian\u00f3polis",
    ],
    PR: ["Curitiba"],
    RS: ["Porto Alegre"],
    SP: ["S\u00e3o Paulo"],
    DF: ["Bras\u00edlia"],
    RJ: ["Rio de Janeiro"],
};

// Atenção: app.py lê este objeto diretamente (load_locality_distances).
// Manter as chaves "UF|Município" entre aspas e os valores numéricos.
const distanciasLocalidadesKm = {
    // Distâncias rodoviárias aproximadas a partir de Lebon Régis, para demonstração acadêmica.
    "SC|Lebon R\u00e9gis": 0,
    "SC|Ca\u00e7ador": 38,
    "SC|Fraiburgo": 32,
    "SC|Curitibanos": 55,
    "SC|Campos Novos": 97,
    "SC|Lages": 146,
    "SC|Chapec\u00f3": 260,
    "SC|Joinville": 288,
    "SC|Blumenau": 260,
    "SC|Florian\u00f3polis": 373,
    "PR|Curitiba": 272,
    "RS|Porto Alegre": 482,
    "SP|S\u00e3o Paulo": 676,
    "DF|Bras\u00edlia": 1661,
    "RJ|Rio de Janeiro": 1118,
};

function normalizarNomeMunicipio(nome) {
    return nome.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

const localidadesBrasil = Object.fromEntries(
    Object.entries(localidadesNomesBrasil).map(([uf, cidades]) => [
        uf,
        cidades.map((nome) => {
            const distancia = Object.prototype.hasOwnProperty.call(distanciasLocalidadesKm, `${uf}|${nome}`)
                ? distanciasLocalidadesKm[`${uf}|${nome}`]
                : null;
            return {
                nome,
                cidade: nome,
                uf,
                distancia_km: distancia,
                distanciaKm: distancia,
                capitalEstadual: uf === "SC" && normalizarNomeMunicipio(nome) === "florianopolis",
                capitalFederal: uf === "DF" && normalizarNomeMunicipio(nome) === "brasilia",
            };
        }),
    ])
);

const nomesEstados = {
    AC: "Acre",
    AL: "Alagoas",
    AP: "Amapá",
    AM: "Amazonas",
    BA: "Bahia",
    CE: "Ceará",
    DF: "Distrito Federal",
    ES: "Espírito Santo",
    GO: "Goiás",
    MA: "Maranhão",
    MT: "Mato Grosso",
    MS: "Mato Grosso do Sul",
    MG: "Minas Gerais",
    PA: "Pará",
    PB: "Paraíba",
    PR: "Paraná",
    PE: "Pernambuco",
    PI: "Piauí",
    RJ: "Rio de Janeiro",
    RN: "Rio Grande do Norte",
    RS: "Rio Grande do Sul",
    RO: "Rondônia",
    RR: "Roraima",
    SC: "Santa Catarina",
    SP: "São Paulo",
    SE: "Sergipe",
    TO: "Tocantins",
};

const campoEstado = document.querySelector("#stateSelect");
const campoCidade = document.querySelector("#citySelect");
const campoDestino = document.querySelector("#destinationInput");
const campoDistanciaDestino = document.querySelector("#destinationDistance");

function definirOpcoes(campo, opcoes, textoInicial) {
    campo.innerHTML = "";
    campo.append(new Option(textoInicial, ""));
    opcoes.forEach((opcao) => campo.append(new Option(opcao.label, opcao.value)));
}

function obterLocalidadeSelecionada() {
    if (!campoEstado?.value || !campoCidade?.value) {
        return null;
    }
    return (localidadesBrasil[campoEstado.value] || []).find(
        (cidade) => cidade.nome === campoCidade.value
    ) || null;
}

function formatarDistanciaDestino(localidade) {
    if (!localidade) {
        return "Distância aproximada de Lebon Régis: -";
    }
    const distancia = localidade.distancia_km;
    if (distancia === null || distancia === undefined || distancia === "") {
        return "Distância aproximada de Lebon Régis: não cadastrada";
    }
    return `Distância aproximada de Lebon Régis: ${Number(distancia).toLocaleString("pt-BR", { maximumFractionDigits: 0 })} km`;
}

function atualizarDistanciaDestino(localidade) {
    if (campoDistanciaDestino) {
        campoDistanciaDestino.textContent = formatarDistanciaDestino(localidade);
    }
}

function atualizarDestino() {
    if (!campoEstado.value || !campoCidade.value) {
        campoDestino.value = "";
        atualizarDistanciaDestino(null);
        document.dispatchEvent(new CustomEvent("localidade:alterada", { detail: null }));
        return;
    }
    const localidade = obterLocalidadeSelecionada();
    campoDestino.value = `${campoCidade.value} - ${campoEstado.value}`;
    atualizarDistanciaDestino(localidade);
    document.dispatchEvent(new CustomEvent("localidade:alterada", { detail: localidade }));
}

function preencherCidades() {
    const uf = campoEstado.value;
    const cidades = (localidadesBrasil[uf] || []).map((cidade) => ({ label: cidade.nome, value: cidade.nome }));

    campoCidade.disabled = cidades.length === 0;
    definirOpcoes(
        campoCidade,
        cidades,
        cidades.length ? "Selecione a cidade" : "Selecione primeiro o estado"
    );
}

if (campoEstado && campoCidade && campoDestino) {
    const estados = Object.keys(localidadesBrasil).map((uf) => ({
        label: `${nomesEstados[uf]} (${uf})`,
        value: uf,
    }));

    definirOpcoes(campoEstado, estados, "Selecione o estado");

    campoEstado.addEventListener("change", () => {
        preencherCidades();
        atualizarDestino();
    });

    campoCidade.addEventListener("change", atualizarDestino);

    if (campoEstado.dataset.initialValue) {
        campoEstado.value = campoEstado.dataset.initialValue;
        preencherCidades();
        campoCidade.value = campoCidade.dataset.initialValue || "";
        atualizarDestino();
    }
}

window.localidadesBrasil = localidadesBrasil;
window.distanciasLocalidadesKm = distanciasLocalidadesKm;
window.obterLocalidadeSelecionada = obterLocalidadeSelecionada;
window.formatarDistanciaDestino = formatarDistanciaDestino;
