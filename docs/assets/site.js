(() => {
  const language = localStorage.getItem("longrun-language") || "zh";
  const applyLanguage = (next) => {
    const language = next;
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    document.body.dataset.language = language;
    document.querySelectorAll("[data-zh][data-en]").forEach((node) => {
      node.textContent = node.dataset[language];
    });
    document.querySelectorAll("[data-lang-toggle]").forEach((button) => {
      button.textContent = language === "zh" ? "English" : "中文";
      button.setAttribute("aria-label", language === "zh" ? "Switch to English" : "切换到中文");
    });
    localStorage.setItem("longrun-language", language);
  };
  applyLanguage(language);
  document.querySelectorAll("[data-lang-toggle]").forEach((button) => {
    button.addEventListener("click", () => applyLanguage(document.body.dataset.language === "zh" ? "en" : "zh"));
  });

  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.querySelectorAll("[data-kind]").forEach((item) => {
        item.hidden = button.dataset.filter !== "all" && item.dataset.kind !== button.dataset.filter;
      });
    });
  });

  document.querySelectorAll("[data-node]").forEach((node) => {
    node.addEventListener("click", () => {
      document.querySelectorAll("[data-node]").forEach((item) => item.classList.remove("selected"));
      node.classList.add("selected");
      const target = document.querySelector("[data-map-detail]");
      if (target) target.textContent = node.getAttribute(`data-${document.body.dataset.language}`);
    });
  });
})();
