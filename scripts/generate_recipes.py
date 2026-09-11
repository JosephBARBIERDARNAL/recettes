from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = ROOT / "recipes"
DOCS_DIR = ROOT / "docs"
CONFIG_PATH = ROOT / "zensical.toml"
INDEX_PATH = DOCS_DIR / "index.md"
FRACTION_GLYPHS = {
    0.25: "¼",
    0.333: "⅓",
    0.5: "½",
    0.667: "⅔",
    0.75: "¾",
}


def escape(value: Any) -> str:
    return html.escape(str(value), quote=False)


def escape_attr(value: Any) -> str:
    return html.escape(str(value), quote=True)


def display_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def format_amount(value: float) -> str:
    rounded = round(float(value), 3)
    whole = int(rounded)
    remainder = round(rounded - whole, 3)

    for fraction, glyph in FRACTION_GLYPHS.items():
        if abs(fraction - remainder) < 0.01:
            return f"{whole}{glyph}" if whole else glyph

    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:g}".replace(".", ",")


def numeric_amount(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def render_amount(ingredient: dict[str, Any], servings: float) -> str:
    amount = ingredient.get("amount")
    unit = str(ingredient.get("unit", ""))
    scalable = ingredient.get("scalable", True)

    if numeric_amount(amount) and scalable:
        amount_value = str(amount).lower()
        amount_label = format_amount(amount)
        if unit:
            amount_label = f"{amount_label} {unit}"
        return (
            '<span class="recipe-ingredient__amount" '
            f'data-base-amount="{escape_attr(amount_value)}" '
            f'data-base-servings="{escape_attr(servings)}" '
            f'data-unit="{escape_attr(unit)}">{escape(amount_label)}</span>'
        )

    if amount is None:
        return ""
    amount_label = str(ingredient.get("amount_label", amount))
    if unit:
        amount_label = f"{amount_label} {unit}"
    return escape(amount_label)


def render_ingredient(ingredient: dict[str, Any], servings: float) -> str:
    amount = render_amount(ingredient, servings)
    name = escape(ingredient.get("name", ""))
    info = ingredient.get("info")
    info_html = (
        f' <span class="recipe-info" title="{escape_attr(info)}">i</span>'
        if info
        else ""
    )
    separator = " " if amount and name else ""
    return f"""          <li class="recipe-ingredient">
            <label>
              <input type="checkbox">
              <span class="recipe-checkmark" aria-hidden="true"></span>
              <span class="recipe-ingredient__text">{amount}{separator}{name}{info_html}</span>
            </label>
          </li>"""


def render_group(group: dict[str, Any], servings: float, recipe_slug: str) -> str:
    title = str(group["title"])
    group_id = f"{slugify(recipe_slug)}-{slugify(title)}-title"
    ingredients = "\n".join(
        render_ingredient(ingredient, servings)
        for ingredient in group.get("ingredients", [])
    )
    return f"""      <section class="ingredient-group" aria-labelledby="{escape_attr(group_id)}">
        <h3 id="{escape_attr(group_id)}">{escape(title)}</h3>
        <ul class="recipe-ingredients-list">
{ingredients}
        </ul>
      </section>"""


def render_recipe(recipe: dict[str, Any], source_path: Path) -> str:
    slug = str(recipe["slug"])
    title = str(recipe["title"])
    description = str(recipe["description"])
    icon = str(recipe["icon"])
    servings = recipe["servings"]
    if not numeric_amount(servings) or float(servings) <= 0:
        raise ValueError(f"{source_path}: servings must be a positive number")

    facts = [
        ("Préparation", recipe["prep_time"], False),
        ("Niveau", recipe["difficulty"], False),
        ("Régime", recipe["diet"], True),
        ("Matériel", recipe["equipment"], False),
    ]
    facts_html = "\n".join(
        f"""      <li class="recipe-fact">
        <span class="recipe-fact__label">{escape(label)}</span>
        <strong{' class="recipe-fact__value--tag"' if tag else ""}>{escape(display_value(value))}</strong>
      </li>"""
        for label, value, tag in facts
    )
    groups_html = "\n\n".join(
        render_group(group, servings, slug)
        for group in recipe.get("ingredient_groups", [])
    )
    steps_html = "\n".join(
        f"""        <li class="recipe-step">
          <span class="recipe-step__number">{index:02d}</span>
          <div>
            <h3>{escape(step["title"])}</h3>
            <p>{escape(step["text"])}</p>
          </div>
        </li>"""
        for index, step in enumerate(recipe.get("steps", []), start=1)
    )
    seasoning = recipe.get("seasoning")
    seasoning_html = (
        f'\n\n      <p class="recipe-card__footnote">{escape(seasoning)}</p>'
        if seasoning
        else ""
    )
    source = source_path.relative_to(ROOT).as_posix()
    front_matter = yaml.safe_dump(
        {"title": title, "description": description, "icon": icon},
        allow_unicode=True,
        sort_keys=False,
    ).strip()

    return f'''---
{front_matter}
---

<!-- Generated from {source}; edit the YAML file instead. -->
<div class="recipe-page" data-recipe-root data-default-servings="{escape_attr(servings)}">
  <header class="recipe-header">
    <div class="recipe-header__title">
      <h1>{escape(title)}</h1>
    </div>
    <ul class="recipe-facts" aria-label="Informations pratiques">
{facts_html}
    </ul>
  </header>

  <div class="recipe-servings-bar" aria-label="Nombre de portions">
    <span class="recipe-servings-bar__label">Pour</span>
    <div class="recipe-stepper">
      <button type="button" class="recipe-stepper__button" data-serving-change="-1" aria-label="Retirer une portion">−</button>
      <output class="recipe-stepper__value" data-servings-output>{escape(servings)}</output>
      <button type="button" class="recipe-stepper__button" data-serving-change="1" aria-label="Ajouter une portion">+</button>
      <span>personnes</span>
    </div>
  </div>

  <div class="recipe-layout">
    <aside class="recipe-card recipe-card--ingredients" aria-labelledby="ingredients-title">
      <div class="recipe-card__heading">
        <p class="recipe-card__eyebrow">À PRÉVOIR</p>
        <h2 id="ingredients-title">Le marché</h2>
        <p class="recipe-card__intro">Sélectionnez les ingrédients au fur et à mesure. Les quantités sont ajustées automatiquement.</p>
      </div>

{groups_html}{seasoning_html}
    </aside>

    <section class="recipe-card recipe-card--method" aria-labelledby="method-title">
      <div class="recipe-card__heading recipe-card__heading--method">
        <p class="recipe-card__eyebrow">LE GESTE</p>
        <h2 id="method-title">En trois temps</h2>
      </div>

      <ol class="recipe-steps">
{steps_html}
      </ol>
    </section>
  </div>
</div>
'''


def load_recipes() -> list[tuple[Path, dict[str, Any]]]:
    paths = sorted((*RECIPES_DIR.glob("*.yaml"), *RECIPES_DIR.glob("*.yml")))
    if not paths:
        raise ValueError(f"No YAML recipes found in {RECIPES_DIR}")

    recipes = []
    slugs = set()
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        required = {
            "slug",
            "title",
            "description",
            "icon",
            "servings",
            "prep_time",
            "difficulty",
            "diet",
            "equipment",
            "ingredient_groups",
            "steps",
        }
        missing = sorted(required - data.keys())
        if missing:
            raise ValueError(f"{path}: missing fields: {', '.join(missing)}")
        slug = str(data["slug"])
        if slug in slugs:
            raise ValueError(f"Duplicate recipe slug: {slug}")
        if slug in {"index", "syntax"}:
            raise ValueError(f"Reserved recipe slug: {slug}")
        slugs.add(slug)
        recipes.append((path, data))
    return sorted(recipes, key=lambda item: str(item[1]["title"]).casefold())


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def update_index(recipes: list[tuple[Path, dict[str, Any]]]) -> str:
    links = "\n".join(
        f"- [{escape(recipe['title'])}]({escape(recipe['slug'])}.md)"
        for _, recipe in recipes
    )
    return f"<!-- Generated by scripts/generate_recipes.py; edit recipes/*.yaml instead. -->\n\n# Recettes\n\n{links}\n"


def update_navigation(recipes: list[tuple[Path, dict[str, Any]]]) -> None:
    config = CONFIG_PATH.read_text(encoding="utf-8")
    entries = ['"Recettes" = "index.md"']
    entries.extend(
        f"{json.dumps(str(recipe['title']), ensure_ascii=False)} = {json.dumps(str(recipe['slug']) + '.md')}"
        for _, recipe in recipes
    )
    nav = "nav = [\n  { " + ", ".join(entries) + " },\n]\n"
    pattern = re.compile(r"^nav = \[\n.*?^\]\n", re.MULTILINE | re.DOTALL)
    updated, count = pattern.subn(nav, config, count=1)
    if count != 1:
        raise ValueError(f"Could not find the nav block in {CONFIG_PATH}")
    write_if_changed(CONFIG_PATH, updated)


def main() -> int:
    try:
        recipes = load_recipes()
        for source_path, recipe in recipes:
            output_path = DOCS_DIR / f"{recipe['slug']}.md"
            changed = write_if_changed(output_path, render_recipe(recipe, source_path))
            status = "updated" if changed else "unchanged"
            print(f"{status}: {output_path.relative_to(ROOT)}")
        write_if_changed(INDEX_PATH, update_index(recipes))
        update_navigation(recipes)
        print(f"generated {len(recipes)} recipe(s)")
        return 0
    except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
