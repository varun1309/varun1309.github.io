# vsrivastava.com

Personal site of Varun Srivastava. A static [Jekyll](https://jekyllrb.com) site
served by GitHub Pages at [vsrivastava.com](https://vsrivastava.com).

No CSS or JS framework: one hand-written stylesheet, no build step for the
front end, and no client-side JavaScript at all.

## Running it locally

```bash
bundle install
bundle exec jekyll serve   # http://localhost:4000
```

Needs Ruby 3.0 or newer. The macOS system Ruby (2.6) is too old — install a
current one with `brew install ruby` or `rbenv`.

## Layout

```
_config.yml                 site config
_layouts/                   default, page, post
_includes/                  head, site-header, site-footer
_posts/                     one file per post
assets/css/main.css         the whole stylesheet
assets/img/                 images
index.html                  home page
blog/index.html             post index
tools/                      scripts, excluded from the build
tools/a4e/                  regenerates the A-4E-C post from a DCS export
```

## Adding a post

Drop a file in `_posts/` named `YYYY-MM-DD-slug.md`:

```markdown
---
title: "Post title"
standfirst: >-
  One or two sentences shown under the title and in the post list.
---

Body in Markdown.
```

`layout: post` is applied automatically. Posts appear on `/blog/` and in the
Writing section of the home page without any further wiring.

### Posts that bring their own stylesheet

A post that ships a complete self-contained design (the A-4E-C guide, for
example) sets `embed: true` in its front matter, which drops the article's
reading-measure constraint. Such a post must scope its own CSS so it cannot
collide with `main.css`: prefix every custom property, and nest every selector
under a wrapper class. `tools/build_post.py` shows how that transformation was
done for the A-4E-C post.

### Generated posts

The A-4E-C post's diagrams and HOTAS tables are generated from JSON under
`tools/a4e/data/`, with the keybind layers driven by a DCS input export. Four
marker-fenced regions of the post are rewritten by `tools/a4e/build.py`;
everything outside them is hand-written.

To refresh it after re-mapping the stick in DCS, see
[`tools/a4e/UPDATING.md`](tools/a4e/UPDATING.md); for how the generator works,
[`tools/a4e/README.md`](tools/a4e/README.md).

## Licence

Code released under the [MIT](LICENSE) licence. Site content and images are not
covered by that licence.
