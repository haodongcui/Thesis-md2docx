from __future__ import annotations

import re


def needs_soft_wrap_space(left: str, right: str) -> bool:
    if not left or not right:
        return False
    left_char = left[-1]
    right_char = right[0]
    return (
        left_char.isascii()
        and right_char.isascii()
        and left_char.isalnum()
        and right_char.isalnum()
    )


def join_soft_wrapped_lines(lines: list[str]) -> str:
    parts: list[tuple[str, bool]] = []
    for line in lines:
        if not line.strip():
            continue
        stripped_right = line.rstrip()
        hard_break = line.endswith("  ") or stripped_right.endswith("\\")
        if stripped_right.endswith("\\"):
            stripped_right = stripped_right[:-1]
        parts.append((stripped_right.strip(), hard_break))

    if not parts:
        return ""
    merged = parts[0][0]
    previous_hard_break = parts[0][1]
    for part, hard_break in parts[1:]:
        separator = "\n" if previous_hard_break else " " if needs_soft_wrap_space(merged.rstrip(), part.lstrip()) else ""
        merged += separator + part
        previous_hard_break = hard_break
    return merged


def split_plain_paragraphs(text: str) -> list[str]:
    paragraphs: list[str] = []
    buffer: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if buffer:
                paragraph = join_soft_wrapped_lines(buffer)
                if paragraph:
                    paragraphs.append(paragraph)
                buffer = []
            continue
        if stripped.startswith(">"):
            stripped = stripped[1:].strip()
        buffer.append(stripped)
    if buffer:
        paragraph = join_soft_wrapped_lines(buffer)
        if paragraph:
            paragraphs.append(paragraph)
    return paragraphs


def parse_markdown_document(text: str) -> tuple[str, dict[str, str], str]:
    lines = text.splitlines()
    title = ""
    front_sections: dict[str, str] = {}
    current_section: str | None = None
    buffer: list[str] = []
    body_start = len(lines)

    for idx, line in enumerate(lines):
        if not title:
            match = re.match(r"^#\s+(.*)$", line)
            if match:
                title = match.group(1).strip()
                continue

        if re.match(r"^#\s+\d+\b", line):
            body_start = idx
            break

        section_match = re.match(r"^##\s+(.*)$", line)
        if section_match:
            if current_section is not None:
                front_sections[current_section] = "\n".join(buffer).strip()
            current_section = section_match.group(1).strip()
            buffer = []
            continue

        if re.fullmatch(r"-{3,}|\*{3,}", line.strip()):
            if current_section is not None:
                front_sections[current_section] = "\n".join(buffer).strip()
                current_section = None
                buffer = []
            continue

        if current_section is not None:
            buffer.append(line)

    if current_section is not None:
        front_sections[current_section] = "\n".join(buffer).strip()

    body_text = "\n".join(lines[body_start:]).strip()
    return title, front_sections, body_text


def parse_cover_info(text: str) -> dict[str, str]:
    info: dict[str, str] = {}
    last_key = ""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(">"):
            continue
        if "：" in stripped:
            key, value = stripped.split("：", 1)
        elif ":" in stripped:
            key, value = stripped.split(":", 1)
        else:
            if last_key:
                info[last_key] = f"{info[last_key]}\n{stripped}" if info[last_key] else stripped
            continue
        last_key = key.strip()
        info[last_key] = value.strip()
    return info


def extract_abstract_and_keywords(text: str, keyword_prefix: str) -> tuple[list[str], str]:
    paragraphs = split_plain_paragraphs(text)
    body: list[str] = []
    keywords = ""
    for paragraph in paragraphs:
        if paragraph.startswith(keyword_prefix):
            keywords = paragraph[len(keyword_prefix):].strip()
        else:
            body.append(paragraph)
    return body, keywords


def extract_abstract_keyword_blocks(text: str, keyword_prefix: str) -> tuple[list[str], str, list[str]]:
    paragraphs = split_plain_paragraphs(text)
    before_keyword: list[str] = []
    after_keyword: list[str] = []
    keywords = ""
    found_keyword = False
    for paragraph in paragraphs:
        if paragraph.startswith(keyword_prefix) and not found_keyword:
            keywords = paragraph[len(keyword_prefix) :].strip()
            found_keyword = True
            continue
        if found_keyword:
            after_keyword.append(paragraph)
        else:
            before_keyword.append(paragraph)
    return before_keyword, keywords, after_keyword


def split_cover_title_lines(title: str) -> list[str]:
    explicit_lines = [re.sub(r"\s+", "", line.strip()) for line in title.splitlines() if line.strip()]
    if len(explicit_lines) > 1:
        return explicit_lines

    compact = re.sub(r"\s+", "", title.strip())
    if not compact:
        return [""]

    def avoid_ascii_word_break(value: str, split_at: int) -> int:
        if not (0 < split_at < len(value)):
            return split_at
        if not (value[split_at - 1].isascii() and value[split_at - 1].isalnum()):
            return split_at
        if not (value[split_at].isascii() and value[split_at].isalnum()):
            return split_at

        left = split_at
        while left > 0 and value[left - 1].isascii() and value[left - 1].isalnum():
            left -= 1
        right = split_at
        while right < len(value) and value[right].isascii() and value[right].isalnum():
            right += 1

        candidates = [pos for pos in (left, right) if 0 < pos < len(value)]
        if not candidates:
            return split_at
        return min(candidates, key=lambda pos: abs(pos - split_at))

    if len(compact) <= 14:
        return [compact]
    if len(compact) <= 28:
        split_at = (len(compact) + 1) // 2
        # Avoid visually awkward breaks inside common compound terms on the cover.
        for phrase in ("自适应", "强化学习", "世界模型"):
            start = compact.find(phrase)
            if start < 0:
                continue
            end = start + len(phrase)
            if start < split_at < end:
                split_at = end
                break
        split_at = avoid_ascii_word_break(compact, split_at)
        return [compact[:split_at], compact[split_at:]]

    lines: list[str] = []
    chunk = 14
    start = 0
    while start < len(compact):
        end = min(len(compact), start + chunk)
        end = avoid_ascii_word_break(compact, end)
        if end <= start:
            end = min(len(compact), start + chunk)
        lines.append(compact[start:end])
        start = end
    return lines
