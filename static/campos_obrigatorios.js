const formularioObrigatorio = document.querySelector("form.form");

function campoVisivelPara(campo) {
    if (campo.id === "departureDate") {
        return document.querySelector("#departureDateDisplay");
    }
    if (campo.id === "returnDate") {
        return document.querySelector("#returnDateDisplay");
    }
    return campo;
}

function mensagemValidacaoPara(campo) {
    if (campo.tagName === "SELECT") {
        return "Selecione uma opção.";
    }
    if (campo.type === "date") {
        return "Selecione uma data.";
    }
    return "Preencha este campo obrigatório.";
}

function containerErroPara(campo) {
    return campoVisivelPara(campo)?.closest("label");
}

function mostrarErro(campo, mensagem) {
    const container = containerErroPara(campo);
    if (!container) {
        return;
    }

    let erro = container.querySelector(".field-error");
    if (!erro) {
        erro = document.createElement("span");
        erro.className = "field-error";
        erro.id = `${campo.id || campo.name}-erro`;
        erro.setAttribute("role", "alert");
        container.append(erro);
    }
    erro.textContent = mensagem;
    campo.setAttribute("aria-describedby", erro.id);
}

function limparErro(campo) {
    const container = containerErroPara(campo);
    container?.querySelector(".field-error")?.remove();
    campo.removeAttribute("aria-describedby");
}

function validarCampoObrigatorio(campo) {
    const campoVisivel = campoVisivelPara(campo);
    const invalido = campo.required && !campo.disabled && !campo.value.trim();
    campoVisivel?.classList.toggle("is-invalid", invalido);
    campo.setAttribute("aria-invalid", String(invalido));
    campoVisivel?.setAttribute("aria-invalid", String(invalido));

    if (invalido) {
        campo.setCustomValidity(mensagemValidacaoPara(campo));
        mostrarErro(campo, mensagemValidacaoPara(campo));
    } else {
        campo.setCustomValidity("");
        limparErro(campo);
    }

    return !invalido;
}

function validarFormularioObrigatorio(formulario) {
    const campos = formulario.querySelectorAll(
        "input[required]:not([type='hidden']), select[required], textarea[required]"
    );
    return Array.from(campos).every(validarCampoObrigatorio);
}

if (formularioObrigatorio) {
    const campos = formularioObrigatorio.querySelectorAll(
        "input[required]:not([type='hidden']), select[required], textarea[required]"
    );

    campos.forEach((campo) => {
        campo.addEventListener("invalid", () => validarCampoObrigatorio(campo));
        campo.addEventListener("blur", () => validarCampoObrigatorio(campo));
        campo.addEventListener("change", () => validarCampoObrigatorio(campo));
        campo.addEventListener("input", () => validarCampoObrigatorio(campo));
    });

    formularioObrigatorio.addEventListener("submit", (evento) => {
        if (!validarFormularioObrigatorio(formularioObrigatorio)) {
            evento.preventDefault();
            const primeiroInvalido = formularioObrigatorio.querySelector(".is-invalid");
            primeiroInvalido?.focus();
        }
    });
}
