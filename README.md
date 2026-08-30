# Daniel Coelho's Blog

Hugo + PaperMod, deployed to <https://1danielcoelho.github.io/> by GitHub Actions.

## New post

1. Create `content/posts/my-post-slug/index.md`. Put any images in that same folder.

   ```markdown
   ---
   title: "My post"
   date: 2026-08-30
   slug: "my-post-slug"
   description: "One line. Used for search results and link previews."
   tags: ["unreal"]
   ---
   ```

2. `hugo server` → <http://localhost:1313> to check it.
3. Commit and push to `main`.

That's it. Pushing to `main` triggers `.github/workflows/hugo.yml`, which builds the
site and publishes it — usually live in about a minute. Nothing is built locally.

### Frontmatter options

| Key | Effect |
|---|---|
| `draft: true` | Keep it out of the published site. `hugo server -D` shows drafts locally. |
| `ShowToc: false` | Hide the table of contents on this post. Worth it for short posts. |
| `TocOpen: true` | Show the ToC expanded instead of collapsed. |
| `ShowReadingTime: false` | Hide the "N min" estimate. |
| `searchHidden: true` | Keep it out of the search index. |
| `robotsNoIndex: true` | Ask search engines not to index it. |

`slug` sets the URL (`/my-post-slug/`). Never change it on an existing post — that
breaks its links.

## Markdown reference

Everything below is verified working on this site.

### Links

```markdown
[link text](https://example.com)
[link with a tooltip](https://example.com "hover text")
<https://example.com>                      bare URL, auto-linked

[another post here]({{< ref "pytorch-conventions" >}})
```

Use `{{< ref "slug" >}}` for links to your own posts rather than typing the URL. It
resolves to the full permalink and **fails the build if the slug doesn't exist**, so
internal links can't silently rot.

### Images

Images live in the post's own folder, so reference them by bare filename:

```markdown
![Alt text describing the image](diagram.png)
```

To make an image click-to-enlarge (the pattern used in the older posts), wrap it in a
link to itself:

```markdown
[![Alt text](diagram.png)](diagram.png)
```

### Code

Inline: `` `FTransform` `` renders as `FTransform`.

Fenced, with a language for syntax highlighting:

````markdown
```cpp
void Foo(const FTransform& Transform)
{
    // highlighted
}
```
````

Use lowercase language names. Ones already in use here: `cpp`, `python`, `rust`,
`json`, `toml`, `ini`, `html`, `batch`, `text`. Use `text` for plain output with no
highlighting. Leaving the language off gives an unhighlighted block.

To show markdown containing a code fence (like this README does), wrap it in **four**
backticks instead of three.

### Quotes

```markdown
> A quote box. Also good for asides, disclaimers and warnings.
>
> Spans multiple paragraphs if you keep the `>`.
```

Note: GitHub-style callouts (`> [!NOTE]`, `> [!WARNING]`) are **not** supported — they
render as an ordinary quote with the literal `[!NOTE]` text visible. Just use a normal
quote with a bolded lead-in:

```markdown
> **Disclaimer:** back up your assets before trying this.
```

### Everything else

```markdown
# Heading      ## Subheading      ### Sub-subheading

**bold**   *italic*   ~~strikethrough~~

- bullet
- list
  - nested with two spaces

1. numbered
2. list

- [ ] unchecked task
- [x] checked task

| Column | Column |
|---|---|
| cell   | cell   |

A claim needing a source.[^1]

[^1]: The footnote, rendered at the bottom of the post.

---
```

(`---` on its own line is a horizontal rule. Don't put it at the very top of the file —
that starts the frontmatter block.)

## Local commands

| Command | What it does |
|---|---|
| `hugo server` | Preview at <http://localhost:1313>, live-reloads on save |
| `hugo server -D` | Same, but includes `draft: true` posts |
| `hugo` | Build into `public/`. Only for checking the build — deploys come from Actions. |

If `hugo` isn't found, restart your shell: winget put it on PATH after this one was
started.

## Setup on a fresh machine

The theme is a git submodule, so clone with it:

```bash
git clone --recursive https://github.com/1danielcoelho/1danielcoelho.github.io.git
```

Already cloned without `--recursive`? `git submodule update --init --recursive`.
