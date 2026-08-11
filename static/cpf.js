function formatarCpf(valor) {
    const digitos = (valor || "").replace(/\D/g, "").slice(0, 11);

    if (digitos.length <= 3) {
        return digitos;
    }
    if (digitos.length <= 6) {
        return `${digitos.slice(0, 3)}.${digitos.slice(3)}`;
    }
    if (digitos.length <= 9) {
        return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6)}`;
    }

    return `${digitos.slice(0, 3)}.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-${digitos.slice(9)}`;
}

document.querySelectorAll(".cpf-mask").forEach((campo) => {
    campo.value = formatarCpf(campo.value);

    campo.addEventListener("input", () => {
        campo.value = formatarCpf(campo.value);
    });

    campo.addEventListener("paste", () => {
        window.setTimeout(() => {
            campo.value = formatarCpf(campo.value);
        }, 0);
    });
});
