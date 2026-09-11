(() => {
  const fractionGlyphs = new Map([
    [0.25, "¼"],
    [0.333, "⅓"],
    [0.5, "½"],
    [0.667, "⅔"],
    [0.75, "¾"],
  ]);

  const formatAmount = (value) => {
    const rounded = Math.round(value * 1000) / 1000;
    const whole = Math.floor(rounded);
    const remainder = Math.round((rounded - whole) * 1000) / 1000;
    const glyph = [...fractionGlyphs.entries()].find(
      ([key]) => Math.abs(key - remainder) < 0.01,
    )?.[1];

    if (glyph && whole > 0) return `${whole}${glyph}`;
    if (glyph) return glyph;
    return rounded.toLocaleString("fr-FR", { maximumFractionDigits: 2 });
  };

  const initialiseRecipe = () => {
    document.querySelectorAll("[data-recipe-root]").forEach((recipe) => {
      if (recipe.dataset.ready === "true") return;
      recipe.dataset.ready = "true";

      const configuredServings = Number(recipe.dataset.defaultServings);
      let servings =
        Number.isFinite(configuredServings) && configuredServings > 0
          ? configuredServings
          : 2;
      const servingsOutput = recipe.querySelector("[data-servings-output]");
      const amountNodes = recipe.querySelectorAll("[data-base-amount]");

      const refreshAmounts = () => {
        if (servingsOutput) servingsOutput.textContent = servings;
        amountNodes.forEach((amountNode) => {
          const baseAmount = Number(amountNode.dataset.baseAmount);
          const baseServings = Number(amountNode.dataset.baseServings || 2);
          const unit = amountNode.dataset.unit;
          const amount = formatAmount((baseAmount / baseServings) * servings);
          amountNode.textContent = unit ? `${amount} ${unit}` : amount;
        });
      };

      recipe.querySelectorAll("[data-serving-change]").forEach((button) => {
        button.addEventListener("click", () => {
          servings = Math.min(
            12,
            Math.max(1, servings + Number(button.dataset.servingChange)),
          );
          refreshAmounts();
        });
      });

      recipe
        .querySelectorAll(".recipe-ingredient input")
        .forEach((checkbox) => {
          checkbox.addEventListener("change", () => {
            checkbox
              .closest(".recipe-ingredient")
              ?.classList.toggle("is-checked", checkbox.checked);
          });
        });

      refreshAmounts();
    });
  };

  if (typeof document$ !== "undefined") {
    document$.subscribe(initialiseRecipe);
  } else {
    document.addEventListener("DOMContentLoaded", initialiseRecipe);
  }
})();
