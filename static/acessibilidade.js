const botaoContraste = document.querySelector("[data-contrast-toggle]");
const chaveContraste = "diariaDigitalAltoContraste";

function aplicarContraste(ativo) {
    document.documentElement.classList.toggle("high-contrast", ativo);

    if (botaoContraste) {
        botaoContraste.setAttribute("aria-pressed", String(ativo));
        botaoContraste.textContent = ativo ? "Contraste normal" : "Alto contraste";
    }
}

aplicarContraste(localStorage.getItem(chaveContraste) === "true");

botaoContraste?.addEventListener("click", () => {
    const ativo = !document.documentElement.classList.contains("high-contrast");
    localStorage.setItem(chaveContraste, String(ativo));
    aplicarContraste(ativo);
});
