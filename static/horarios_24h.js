const camposHorario24h = document.querySelectorAll(".time-24");

camposHorario24h.forEach((campo) => {
    campo.addEventListener("input", () => {
        const digitos = campo.value.replace(/\D/g, "").slice(0, 4);
        if (digitos.length <= 2) {
            campo.value = digitos;
            return;
        }
        campo.value = `${digitos.slice(0, 2)}:${digitos.slice(2, 4)}`;
    });

    campo.addEventListener("blur", () => {
        if (!campo.value) {
            campo.setCustomValidity("");
            campo.classList.remove("is-invalid");
            return;
        }

        const [horas, minutos] = campo.value.split(":").map(Number);
        if (
            Number.isNaN(horas) ||
            Number.isNaN(minutos) ||
            horas > 23 ||
            minutos > 59 ||
            campo.value.length !== 5
        ) {
            campo.setCustomValidity("Informe um hor?rio v?lido no formato 24 horas HH:MM.");
            campo.classList.add("is-invalid");
            campo.reportValidity();
            return;
        }

        campo.setCustomValidity("");
        campo.classList.remove("is-invalid");
    });
});
