/* Navigation and reading remain available without JavaScript. */
(() => {
  const root = document.documentElement;
  const preference = matchMedia("(prefers-color-scheme: dark)");
  const readTheme = () => {
    try {
      return localStorage.getItem("book-theme");
    } catch {
      return null;
    }
  };
  const applyTheme = () => {
    const saved = readTheme();
    root.dataset.theme =
      saved === "light" || saved === "dark"
        ? saved
        : preference.matches
          ? "dark"
          : "light";
  };
  applyTheme();
  preference.addEventListener("change", applyTheme);
  document.querySelectorAll(".theme-toggle").forEach((button) => {
    button.hidden = false;
    button.addEventListener("click", () => {
      const theme = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = theme;
      try {
        localStorage.setItem("book-theme", theme);
      } catch {
        /* Session only. */
      }
    });
  });
  document.querySelectorAll("[data-copy]").forEach((button) => {
    button.hidden = false;
    button.addEventListener("click", async () => {
      const status = button.parentElement.querySelector('[role="status"]');
      const url = new URL(location.href);
      url.hash = "";
      try {
        await navigator.clipboard.writeText(url.href);
        status.textContent = button.dataset.copied;
      } catch {
        status.textContent = button.dataset.failed;
      }
    });
  });
})();
