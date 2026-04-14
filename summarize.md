# Reusable Prompt for Summarizing Medium-Style Posts

Summarize the following article into a version that can be read in under 10 minutes. Write the output in Brazilian Portuguese, but keep technical terms in English when needed for accuracy. Preserve the original narrative voice exactly. The text under `## Resumo` must itself be readable in about 10 minutes. Preserve any sections and subsections within the article, summarizing them as well. The final output must contain exactly one `## Resumo` section and exactly one `## Principais insights` section, with no other top-level sections, along with sub sections from the article itself if any. Ignore any site UI or chrome text such as report-problem labels, buttons, footer links, donation links, or navigation elements. Do not produce commentary about code, HTML, markup, prompt instructions, environment variables, setup steps, or tooling details unless those topics are actually part of the article itself. End `## Principais insights` with bullet points only.

## Hard Requirements

1. Write the output in Brazilian Portuguese.
2. Preserve technical terms in English whenever translating them would reduce precision or sound unnatural in technical context.
3. Do **not** change the narrative person or voice of the original text.

   * If the source speaks directly, keep that direct voice.
   * If the source is impersonal, keep it impersonal.
   * Do **not** turn the result into a review, critique, commentary, or meta-description of the post.
   * Do **not** write phrases such as "the article says," "the author argues," or "this post explains," unless that framing already exists in the original.
4. Preserve the original meaning, central argument, and logical flow, but compress it.
5. Remove repetition, non-essential examples, promotional passages, calls to action, and filler.
6. Keep the summary clear, natural, and easy to scan.
7. There must be **only one** `## Resumo` section.
   1. If there are other sections and subsections in the article, write all of them translated under `## Resumo` section, obeying translation rulings written within this file.
8. There must be **only one** `## Principais insights` section.
9. `## Principais insights` must be written with bullet points only.
10. Do **not** create any other top-level sections besides those two.
11. Do **not** copy navigation, footer, modal, CTA, form, legal, donation, or UI text from the site chrome. Ignore elements such as "Reportar um Problema", "Reportando um Problema", "Follow", "Go to the original", "Report problems" donation links, footer links, dark mode toggles, and similar non-article interface text.
12. Do **not** leak or mention prompt instructions, HTML, markup, code structure, CSS classes, setup instructions, environment variables, API keys, local services, model names, or tooling details unless those topics are genuinely part of the source article itself.
13. Do **not** output setup guides, prerequisites, command lines, variable names such as `ANTHROPIC_BASE_URL` or `ANTHROPIC_API_KEY`, or operational instructions unrelated to the article content.
14. Do **not** let the article title bias the style of the output. Even if the title mentions words like `Code`, `Claude`, `Ollama`, `Skill`, `Workflow`, `Setup`, or other technical/tooling terms, still summarize the article itself instead of turning the response into a tutorial, breakdown, categorization, or instruction manual.
15. Do **not** start with phrases such as "Okay, here's a breakdown", "Overview", "Introduction", "Technical setup", "Prerequisites", "Environment variables", "Running", "categorized for clarity", or similar explainer/tutorial framing unless the article itself is literally written in that format and tone.
16. Never transform the article into a step-by-step guide, checklist, categorized breakdown, or documentation-style answer unless the article's original narrative is already explicitly written that way.

## Required Output Format

```md
## Resumo

[Condensed summary in Brazilian Portuguese, short enough to be read in about 10 minutes.]

## Principais insights

* [Insight 1]
* [Insight 2]
* [Insight 3]
```
