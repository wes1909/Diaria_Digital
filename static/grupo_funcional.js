const seletorPerfil = document.querySelector("select[name='role']");
const campoGrupoFuncional = document.querySelector("#dailyGroupField");
const seletorGrupoFuncional = document.querySelector("#dailyGroup");

function atualizarGrupoFuncional() {
    if (!seletorPerfil || !campoGrupoFuncional || !seletorGrupoFuncional) {
        return;
    }

    const aplicaAoPerfil = seletorPerfil.value === "solicitante";
    campoGrupoFuncional.hidden = !aplicaAoPerfil;
    seletorGrupoFuncional.disabled = !aplicaAoPerfil;
    seletorGrupoFuncional.required = aplicaAoPerfil;
    seletorGrupoFuncional.setAttribute("aria-required", String(aplicaAoPerfil));
}

if (seletorPerfil && campoGrupoFuncional && seletorGrupoFuncional) {
    atualizarGrupoFuncional();
    seletorPerfil.addEventListener("change", atualizarGrupoFuncional);
}
