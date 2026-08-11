document.querySelectorAll(".info-tooltip").forEach((tooltip) => {
    tooltip.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        document.querySelectorAll(".info-tooltip.is-open").forEach((opened) => {
            if (opened !== tooltip) {
                opened.classList.remove("is-open");
            }
        });

        tooltip.classList.toggle("is-open");
    });

    tooltip.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            tooltip.classList.remove("is-open");
            tooltip.blur();
        }
    });
});

document.addEventListener("click", () => {
    document.querySelectorAll(".info-tooltip.is-open").forEach((tooltip) => {
        tooltip.classList.remove("is-open");
    });
});
