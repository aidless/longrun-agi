const buttons = document.querySelectorAll("[data-filter]");
const packages = document.querySelectorAll("[data-package]");
buttons.forEach((button) => button.addEventListener("click", () => {
  buttons.forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  packages.forEach((card) => {
    card.hidden = button.dataset.filter !== "all" && card.dataset.kind !== button.dataset.filter;
  });
}));
