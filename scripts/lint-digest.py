#!/usr/bin/env python3
"""Check the digest's machine-readable contract without fetching source links."""

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


@dataclass
class Element:
    tag: str
    attrs: dict
    line: int = 1
    children: list = field(default_factory=list)
    parts: list = field(default_factory=list)

    @property
    def text(self):
        return "".join(self.parts).strip()

    def find(self, tag=None, css_class=None):
        matches = []
        for child in self.children:
            if (tag is None or child.tag == tag) and (
                css_class is None or css_class in child.attrs.get("class", "").split()
            ):
                matches.append(child)
            matches.extend(child.find(tag, css_class))
        return matches


class DigestParser(HTMLParser):
    # HTML validation runs separately; this parser only extracts contract fields.
    VOID = set("area base br col embed hr img input link meta param source track wbr".split())

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element("document", {})
        self.stack = [self.root]
        self.comments = []

    def handle_starttag(self, tag, attrs):
        node = Element(tag, dict(attrs), self.getpos()[0])
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node.parts.append(data)

    def handle_comment(self, data):
        self.comments.append(data)


MONTH_PATTERN = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)
MONTHS = {name: index for index, name in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1
)}
DATE_ENDPOINT = re.compile(
    rf"(?:(?P<period>early|mid|late)[ -]+)?(?P<month>{MONTH_PATTERN})"
    r"(?:\s+(?P<day>\d{1,2}))?", re.IGNORECASE
)


def sort_date(text, year):
    """Return (group, earliest start, latest start); None means an unbounded side.

    Ranges sort on their start, not their duration. Approximate (~) dates have no
    defined tolerance, so do not invent one. Early/mid/late use AGENTS.md's keys.
    """
    text = text.strip()
    qualifier = re.match(r"^(on or before|on or after|before|after|by)\s+|^(~)\s*", text, re.I)
    bound = ""
    if qualifier:
        bound = (qualifier[1] or qualifier[2]).lower()
        text = text[qualifier.end():]
    match = DATE_ENDPOINT.match(text)
    if not match:
        raise ValueError(f"unsupported date label {text!r}")
    month = MONTHS[match["month"][:3].lower()]
    period, day = match["period"], match["day"]
    tail = text[match.end():].strip()
    if not period and not day:
        if not bound and tail.lower() in ("", "(ongoing)"):
            return 2, None, None
        raise ValueError(f"unsupported date label {text!r}")
    if period and day:
        raise ValueError(f"unsupported date label {text!r}")
    first = date(year, month, int(day) if day else {"early": 5, "mid": 15, "late": 25}[period.lower()])
    if tail:
        end_match = re.fullmatch(r"(?:–|-|→)\s*(.+)", tail)
        if not end_match:
            raise ValueError(f"unsupported date label {text!r}")
        endpoint = end_match[1]
        if re.fullmatch(r"\d{1,2}", endpoint):
            last = date(year, month, int(endpoint))
        else:
            end_group, lower, upper = sort_date(endpoint, year)
            if end_group != 0 or lower is None or lower != upper:
                raise ValueError(f"unsupported range endpoint {endpoint!r}")
            last = lower
        if last < first:
            raise ValueError(f"range ends before it starts: {text!r}")
    if bound == "~":
        return 0, None, None
    if bound in ("by", "on or before", "before"):
        return 0, None, first - timedelta(days=bound == "before")
    if bound in ("after", "on or after"):
        return 0, first + timedelta(days=bound == "after"), None
    return 0, first, first


def chronology_errors(month, year):
    """Check all earlier cards, including inversions hidden by ambiguous dates."""
    errors = []
    highest_group = None
    greatest_lower = None

    def describe(card):
        headings, dates = card.find("h3"), card.find(css_class="date")
        title = headings[0].text if headings else "untitled card"
        label = dates[0].text if dates else "missing date"
        return f'{title!r} ({label}, line {card.line})'

    for card in month.find(css_class="ev"):
        dates = card.find(css_class="date")
        if len(dates) != 1 or not dates[0].text:
            continue  # The card contract reports missing/duplicate dates separately.
        try:
            group, lower, upper = sort_date(dates[0].text, year)
            roundup = card.attrs.get("data-roundup", "false")
            if roundup not in ("true", "false"):
                raise ValueError('data-roundup must be "true" or "false"')
            if roundup == "true":
                if group == 2:
                    raise ValueError("a roundup needs a dated window")
                group = 1
        except ValueError as error:
            errors.append(f"digest.html:{card.line}: {error}")
            continue

        previous = None
        if highest_group is not None and group < highest_group[0]:
            previous = highest_group[1]
        elif group == 0 and upper is not None and greatest_lower is not None and greatest_lower[0] > upper:
            previous = greatest_lower[1]
        if previous is not None:
            errors.append(
                f"digest.html:{card.line}: definite inversion: {describe(card)} "
                f"must precede {describe(previous)}"
            )
        if highest_group is None or group > highest_group[0]:
            highest_group = group, card
        if group == 0 and lower is not None and (greatest_lower is None or lower > greatest_lower[0]):
            greatest_lower = lower, card
    return errors


def lint(digest, manifest):
    """Return actionable errors; labels and URLs do not prove factual accuracy."""
    errors = []
    try:
        start = date.fromisoformat(manifest["coverage_start"])
        end = date.fromisoformat(manifest["coverage_end"])
        if start > end:
            errors.append("manifest.json: coverage_start is after coverage_end")
        revision = manifest["revision"]
        if type(revision) is not int or revision < 1:
            errors.append("manifest.json: revision must be a positive integer")
        if not isinstance(manifest["updated_by"], str) or not manifest["updated_by"].strip():
            errors.append("manifest.json: updated_by must be a nonempty string")
        updated = datetime.fromisoformat(manifest["updated_at"].replace("Z", "+00:00"))
        if updated.tzinfo is None:
            errors.append("manifest.json: updated_at must include a timezone")
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        return [f"manifest.json: invalid or missing metadata ({error})"]
    if errors:
        return errors

    parser = DigestParser()
    parser.feed(digest)
    parser.close()
    root = parser.root
    for name, expected in (("coverage-start", start.isoformat()), ("coverage-end", end.isoformat())):
        values = [node.attrs.get("content") for node in root.find("meta") if node.attrs.get("name") == name]
        if values != [expected]:
            errors.append(f"digest.html: expected exactly one {name} meta tag with content {expected}")

    coverage = f"Coverage: {start} through {end}."
    instruction_blocks = [comment for comment in parser.comments if "INSTRUCTIONS FOR CLAUDE" in comment]
    if len(instruction_blocks) != 1 or coverage not in instruction_blocks[0]:
        errors.append("digest.html: instructional comment is missing or its coverage disagrees with manifest")

    for name, nodes in (("title", root.find("title")), ("patch label", root.find(css_class="patch-label")), ("footer", root.find("footer"))):
        if len(nodes) != 1 or re.findall(r"\bv(\d+)\b", nodes[0].text) != [str(revision)]:
            errors.append(f"digest.html: {name} must carry manifest revision v{revision}")
    labels = root.find(css_class="patch-label")
    if len(labels) == 1 and f"covers {start} → {end}" not in labels[0].text:
        errors.append("digest.html: patch label coverage disagrees with manifest")

    months = root.find("section", "month")
    cards = root.find(css_class="ev")
    if not months or not cards:
        errors.append("digest.html: expected month sections containing event cards")
    month_cards = [card for month in months for card in month.find(css_class="ev")]
    if len(month_cards) != len(cards):
        errors.append("digest.html: every event card must belong to exactly one month section")
    for month in months:
        explicit_year = month.attrs.get("data-year")
        if explicit_year is not None and not re.fullmatch(r"\d{4}", explicit_year):
            errors.append(f"digest.html:{month.line}: data-year must be a four-digit year")
        elif explicit_year is None and start.year != end.year:
            errors.append(f"digest.html:{month.line}: multi-year coverage needs data-year on each month section")
        else:
            errors.extend(chronology_errors(month, int(explicit_year) if explicit_year else start.year))

    for card in cards:
        location = f"digest.html:{card.line}"
        for name, nodes in (("heading", card.find("h3")), ("date", card.find(css_class="date"))):
            if len(nodes) != 1 or not nodes[0].text:
                errors.append(f"{location}: card needs exactly one nonempty {name}")
        chips = card.find(css_class="chip")
        if len(chips) != 1 or chips[0].text not in ("CONFIRMED", "REPORTED"):
            errors.append(f"{location}: card needs exactly one CONFIRMED or REPORTED chip")
        else:
            expected = "c" if chips[0].text == "CONFIRMED" else "r"
            classes = chips[0].attrs.get("class", "").split()
            if expected not in classes or ({"c", "r"} - {expected}).intersection(classes):
                errors.append(f"{location}: status chip class disagrees with its label")
        sources = [link for source in card.find(css_class="src") for link in source.find("a")]
        if not sources:
            errors.append(f"{location}: card needs at least one source link in .src")
        for link in sources:
            url = urlsplit(link.attrs.get("href", ""))
            if url.scheme not in ("http", "https") or not url.netloc or not link.text:
                errors.append(f"digest.html:{link.line}: source needs an absolute HTTP(S) URL and link text")
    return errors


def main():
    repo = Path(__file__).resolve().parent.parent
    try:
        manifest = json.loads((repo / "manifest.json").read_text(encoding="utf-8"))
        digest = (repo / "digest.html").read_text(encoding="utf-8")
        errors = lint(digest, manifest)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Digest metadata, card labels, dates, source links, and chronology passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
