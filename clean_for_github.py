#!/usr/bin/env python3
"""
Clean the translated chapter markdown files so they render nicely
in the GitHub mobile app (which strips <style> tags and class attributes).

Source files are already Vietnamese-translated but contain heavy WordPress
HTML (nested <div>, <span>, <style>, decorative boxes). This script produces
a stripped-down markdown that reads well anywhere.

Output goes to `readable/` alongside the source files.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

REPO = Path(__file__).parent
OUT_DIR = REPO / "readable"

CHAPTERS = [
    "chuong-1-anh-sang-thien-phu.md",
    "chuong-2-diem-toi-han-cua-anh-sang-va-bong-toi.md",
    "chuong-3-ban-chat-cua-bong-toi.md",
    "chuong-4-ban-chat-cua-anh-sang.md",
    "chuong-5-tinh-hai-mat-cua-anh-sang-va-bong-toi.md",
    "chuong-6-bong-toi-an-mon-anh-sang.md",
    "chuong-7-diem-khoi-nguon-cua-anh-sang-va-bong-toi.md",
    "chuong-8-diem-den-cuoi-cung-cua-anh-sang-va-bong-toi.md",
]


# --- helpers ---------------------------------------------------------------

BOLD_CLASSES = {
    "bold-red", "bold-blue", "bold-green",
    "emphasis-red", "cocoon-custom-text-1",
    "red", "purple",
    "generic-elegant-title__accent",
    "generic-elegant-title__main",
    "gifted-core-box__em",
    "generic-core-box__em",
    "dark-incident-box__big",
}

FZ_RE = re.compile(r"^fz-(\d+)px$")


def classify_span(class_attr: str) -> str:
    """Return 'heading' | 'bold' | 'plain' based on the class list."""
    classes = class_attr.split()
    bold = any(c in BOLD_CLASSES for c in classes)
    fz = 0
    for c in classes:
        m = FZ_RE.match(c)
        if m:
            fz = max(fz, int(m.group(1)))
    if fz >= 40:
        return "heading"
    if fz >= 28 or bold:
        return "bold"
    return "plain"


def strip_style_blocks(text: str) -> str:
    text = re.sub(r"<style\b[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text


def extract_body(text: str) -> tuple[str, str]:
    """
    Return (h1_title, body_content).

    The pandoc-generated file has the structure:
        <div id="main"> ... <div class="header ..."> ... # Title ... </div>
        <div class="entry-content cf" ...> ... BODY ... </div>
        <div class="entry-categories-tags ..."> ... share/footer junk ... </div>
    """
    # H1 title
    m = re.search(r"^# (.+)$", text, flags=re.MULTILINE)
    title = m.group(1).strip() if m else ""

    # Body: from `entry-content cf` marker to `entry-categories-tags` marker.
    start = re.search(r'<div class="entry-content cf"[^>]*>', text)
    end = re.search(r'<div class="entry-categories-tags', text)
    if start and end:
        body = text[start.end():end.start()]
    else:
        body = text
    return title, body


def convert_figures(text: str) -> str:
    """Convert <figure>...<img src=X>...<figcaption>Y</figcaption>?...</figure> to ![Y](X).

    Handles the common patterns produced by pandoc from the source HTML,
    including <figure> wrappers around tables (in which case we keep
    the inner <table> intact and drop the <figure> wrapper).
    """

    def figure_repl(match: re.Match) -> str:
        inner = match.group(1)
        # If the figure wraps a table, keep the table and turn the caption
        # (if any) into italic text after the table.
        if re.search(r"<table\b", inner, re.IGNORECASE):
            cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", inner, flags=re.DOTALL)
            table_only = re.sub(
                r"<figcaption[^>]*>.*?</figcaption>", "", inner, flags=re.DOTALL
            )
            if cap:
                cap_text = re.sub(r"<[^>]+>", "", cap.group(1))
                cap_text = re.sub(r"\s+", " ", cap_text).strip()
                if cap_text:
                    return f"{table_only}\n\n*{cap_text}*\n\n"
            return table_only
        img = re.search(r'<img[^>]*\bsrc="([^"]+)"[^>]*>', inner)
        if not img:
            return ""  # figure without an image is likely decorative
        src = img.group(1)
        cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", inner, flags=re.DOTALL)
        alt = ""
        if cap:
            alt = re.sub(r"<[^>]+>", "", cap.group(1))
            alt = re.sub(r"\s+", " ", alt).strip()
        return f"\n\n![{alt}]({src})\n\n"

    return re.sub(
        r"<figure\b[^>]*>(.*?)</figure>",
        figure_repl,
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )


def convert_bare_images(text: str) -> str:
    def img_repl(match: re.Match) -> str:
        tag = match.group(0)
        src_m = re.search(r'\bsrc="([^"]+)"', tag)
        alt_m = re.search(r'\balt="([^"]*)"', tag)
        if not src_m:
            return ""
        alt = alt_m.group(1) if alt_m else ""
        return f"![{alt}]({src_m.group(1)})"

    return re.sub(r"<img\b[^>]*/?>", img_repl, text)


def unwrap_spans(text: str) -> str:
    """Iteratively replace the innermost `<span class="...">X</span>` with
    the appropriate markdown emphasis. Innermost first so nesting works."""
    inner_re = re.compile(
        r'<span\s+class="([^"]+)"[^>]*>((?:(?!<span\b|</span>).)*?)</span>',
        flags=re.DOTALL,
    )
    plain_re = re.compile(
        r'<span\b[^>]*>((?:(?!<span\b|</span>).)*?)</span>',
        flags=re.DOTALL,
    )
    changed = True
    guard = 0
    while changed and guard < 40:
        changed = False
        guard += 1

        def repl(m: re.Match) -> str:
            classes = m.group(1)
            content = m.group(2)
            kind = classify_span(classes)
            # Preserve outer whitespace so adjacent spans stay separated
            lead_m = re.match(r"^(\s*)(.*?)(\s*)$", content, flags=re.DOTALL)
            if not lead_m:
                return content
            lead, mid, trail = lead_m.groups()
            if not mid:
                return content
            # Detect if the inner content was already promoted by an inner span
            already_heading = bool(re.match(r"^#{2,4}\s", mid))
            already_bold = bool(re.match(r"^\*\*(?!\s).+?\*\*$", mid, re.DOTALL))
            if kind == "heading":
                if already_heading:
                    return f"\n\n{mid}\n\n"
                # Strip a wrapping **...** so we don't emit "### **text**" -> "**### text**" mess
                inner = mid[2:-2].strip() if already_bold else mid
                return f"\n\n### {inner}\n\n"
            if kind == "bold":
                if already_heading or already_bold:
                    return f"{lead}{mid}{trail}"
                # If inner content already contains `**` markers (nested bold),
                # strip them - the outer bold already covers everything, and
                # nested `**` inside `**...**` breaks markdown parsing.
                if "**" in mid:
                    mid = re.sub(r"\*\*", "", mid)
                return f"{lead}**{mid}**{trail}"
            return content

        new_text, n = inner_re.subn(repl, text)
        if n > 0:
            text = new_text
            changed = True
            continue
        # Fallback: any remaining <span> without class - just unwrap
        new_text, n = plain_re.subn(lambda m: m.group(1), text)
        if n > 0:
            text = new_text
            changed = True
    return text


def strip_link_icons(text: str) -> str:
    """<a>...<span class="fas fa-..." ...></span>...</a> icons already unwrapped;
    empty <a> icons are common. Strip anchors that are empty after cleanup."""
    text = re.sub(r"<a\b[^>]*>\s*</a>", "", text)
    return text


def convert_links(text: str) -> str:
    """<a href="X">Y</a> -> [Y](X). Multiline safe. Skips anchors with no text."""

    def repl(m: re.Match) -> str:
        href = m.group(1)
        inner = m.group(2)
        # If inner still contains block-level tags, leave it alone (will be unwrapped).
        text_only = re.sub(r"<[^>]+>", "", inner)
        text_only = re.sub(r"\s+", " ", text_only).strip()
        if not text_only:
            return ""
        return f"[{text_only}]({href})"

    return re.sub(
        r'<a\b[^>]*\bhref="([^"]+)"[^>]*>(.*?)</a>',
        repl,
        text,
        flags=re.DOTALL,
    )


def unwrap_divs(text: str) -> str:
    """Drop every <div ...> and </div> tag; keep contents."""
    text = re.sub(r"<div\b[^>]*>", "", text)
    text = re.sub(r"</div>", "", text)
    return text


def strip_leftover_tags(text: str) -> str:
    # Drop <colgroup>, <col ...>, <br /> becomes newline, empty <p></p>, <hr>
    text = re.sub(r"<colgroup>.*?</colgroup>", "", text, flags=re.DOTALL)
    text = re.sub(r"<col\b[^>]*/?>", "", text)
    text = re.sub(r"<br\s*/?>", "  \n", text)
    text = re.sub(r"<p>\s*</p>", "", text)

    # Strip class / style / itemprop / role / etc. from tags we keep (table, tr, td, th, tbody, thead)
    def strip_attrs(m: re.Match) -> str:
        name = m.group(1)
        return f"<{name}>"

    text = re.sub(
        r"<(table|thead|tbody|tr|td|th|figcaption)\b[^>]*>",
        strip_attrs,
        text,
        flags=re.IGNORECASE,
    )
    return text


def collapse_bold_collisions(text: str) -> str:
    """Fix `****` artifacts introduced when a span is wrapped in outer `**...**`
    markdown, or when consecutive bold spans meet.

    - `****inner****` (bold-in-bold) collapses to `**inner**`, but only when
      the outer `****` sits at a phrase boundary (start/end of line,
      whitespace, or punctuation). Otherwise the `****` sequence marks
      two adjacent bold runs and should be merged.
    - Any remaining `****` between word characters merges into one bold run.
    """
    # Boundary-anchored collapse: `****X****` where outer `****` is NOT
    # preceded/followed by a word character (i.e. it's the boundary of a bold run).
    for _ in range(3):
        new_text = re.sub(
            r"(?<!\w)\*{4}([^*]+?)\*{4}(?!\w)",
            r"**\1**",
            text,
        )
        if new_text == text:
            break
        text = new_text
    # Any remaining `****` are between two adjacent bold runs -> merge.
    text = re.sub(r"\*{4,}", "", text)
    return text


def collapse_blank_lines(text: str) -> str:
    # Collapse runs of >2 newlines to exactly 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Trim leading/trailing whitespace
    return text.strip() + "\n"


def clean(text: str) -> str:
    title, body = extract_body(text)
    body = strip_style_blocks(body)
    body = convert_figures(body)
    body = convert_bare_images(body)
    body = unwrap_spans(body)
    body = convert_links(body)
    body = strip_link_icons(body)
    body = unwrap_divs(body)
    body = strip_leftover_tags(body)
    body = collapse_bold_collisions(body)
    body = collapse_blank_lines(body)

    header = f"# {title}\n\n" if title else ""
    return header + body


# --- main -----------------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for name in CHAPTERS:
        src = REPO / name
        if not src.exists():
            print(f"skip: {name} (missing)")
            continue
        raw = src.read_text(encoding="utf-8")
        cleaned = clean(raw)
        (OUT_DIR / name).write_text(cleaned, encoding="utf-8")
        print(f"wrote: readable/{name}  ({len(cleaned):,} chars, was {len(raw):,})")


if __name__ == "__main__":
    main()
