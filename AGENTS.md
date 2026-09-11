# Ajouter une recette

Les recettes sont définies dans `recipes/` au format YAML. Il n'est pas nécessaire d'écrire une page Markdown ou de modifier la navigation manuellement.

## 1. Créer le fichier YAML

Créer un fichier `recipes/<slug>.yaml`, avec un `slug` unique en minuscules et séparé par des tirets. Les slugs `index` et `syntax` sont réservés.

Structure minimale :

```yaml
slug: gratin-de-legumes
title: Gratin de légumes
description: "Un gratin simple et doré."
icon: lucide/carrot
servings: 4
prep_time: 20 min
difficulty: Facile
diet: Végétarien
equipment: Four
seasoning: Sel et poivre, selon le goût.

ingredient_groups:
  - title: Pour le gratin
    ingredients:
      - amount: 2
        unit: pièces
        name: courgettes
      - amount: 20
        unit: cl
        name: de crème
        info: "Utiliser une crème entière pour une texture plus onctueuse"

steps:
  - title: Préparer les légumes
    text: "Lavez puis découpez les légumes."
  - title: Cuire
    text: "Enfournez jusqu'à ce que le gratin soit doré."
```

Les champs obligatoires sont `slug`, `title`, `description`, `icon`, `servings`, `prep_time`, `difficulty`, `diet`, `equipment`, `ingredient_groups` et `steps`.

Pour les quantités, utilisez un `amount` numérique : elles seront automatiquement ajustées avec le sélecteur du nombre de personnes. `unit` est facultatif. Pour une quantité textuelle ou non ajustable, utilisez `scalable: false` et éventuellement `amount_label` :

```yaml
- amount: "selon le goût"
  name: sel
  scalable: false
  amount_label: "au goût"
```

## 2. Générer et vérifier

Depuis la racine du projet :

```bash
uv run --with pyyaml python scripts/generate_recipes.py
uvx zensical build --clean
```

Le générateur crée ou met à jour automatiquement `docs/<slug>.md`, `docs/index.md` et la navigation de `zensical.toml`. Ces fichiers sont générés : modifier le YAML source plutôt que leur contenu directement.

Pour travailler avec un serveur local :

```bash
just preview
```

La CI régénère les pages et construit le site automatiquement lorsqu'une modification est poussée sur `main` ou `master`.
