#!/usr/bin/env python3
"""
Validate story data integrity against the lexicon and check structural correctness.

Usage:
    python3 scripts/validate.py            # show only stories with issues + summary
    python3 scripts/validate.py --verbose  # show full stats for every story

Reads:
    data/lexicon.json      — canonical vocabulary
    data/index.json        — story manifest
    data/stories/*.json    — individual story files

Exit code:
    0 — no errors (warnings are OK)
    1 — one or more errors found
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEXICON_FILE = ROOT / "data" / "lexicon.json"
INDEX_FILE = ROOT / "data" / "index.json"
STORIES_DIR = ROOT / "data" / "stories"

# Regex for valid story IDs
ID_PATTERN = re.compile(r"^hsk\d+-\w[\w-]+$")

# Characters treated as punctuation (pinyin and translation must be null)
PUNCTUATION_RE = re.compile(
    r"^[\u3000-\u303f\uff00-\uffef\u2000-\u206f"
    r"\u0021-\u002f\u003a-\u0040\u005b-\u0060\u007b-\u007e]+$"
)


def is_punctuation(text):
    """Return True if the token text is purely punctuation."""
    return bool(PUNCTUATION_RE.match(text))


# ── Collectors ──

class Issues:
    """Accumulate errors and warnings with typed tags."""

    def __init__(self):
        self.errors = []   # list of (tag, message)
        self.warnings = []

    def error(self, tag, msg):
        self.errors.append((tag, msg))

    def warn(self, tag, msg):
        self.warnings.append((tag, msg))

    @property
    def has_errors(self):
        return len(self.errors) > 0

    @property
    def has_issues(self):
        return len(self.errors) + len(self.warnings) > 0


# ── Loading ──

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data():
    """Load lexicon, index, and all story files. Returns (lexicon, index, stories dict)."""
    lexicon = load_json(LEXICON_FILE)
    index = load_json(INDEX_FILE)

    # Build a map of story ID → (story_data, index_entry, level_id)
    stories = {}
    for level in index.get("levels", []):
        for entry in level.get("stories", []):
            story_path = ROOT / "data" / entry["file"]
            if story_path.exists():
                stories[entry["id"]] = {
                    "data": load_json(story_path),
                    "index_entry": entry,
                    "level_id": level["id"],
                }

    return lexicon, index, stories


# ── Index validation ──

def validate_index(index, issues):
    """Validate index.json structure (section 2)."""
    # Required top-level keys
    for key in ("genres", "levels"):
        if key not in index:
            issues.error("index-missing-key", f'index.json missing required key "{key}"')

    genres = index.get("genres", {})
    levels = index.get("levels", [])

    if not isinstance(genres, dict):
        issues.error("index-bad-genres", "index.json genres must be an object")
        return set()

    if not isinstance(levels, list):
        issues.error("index-bad-levels", "index.json levels must be a list")
        return set()

    referenced_files = set()

    for level in levels:
        # Level structure
        lid = level.get("id", "")
        if not re.match(r"^hsk\d+$", lid):
            issues.error("index-bad-level-id", f'Level id "{lid}" does not match hsk\\d+')

        for key in ("id", "name", "stories"):
            if key not in level:
                issues.error("index-level-missing-key", f'Level missing key "{key}"')

        story_list = level.get("stories", [])
        if not isinstance(story_list, list):
            issues.error("index-bad-stories", f'Level {lid} stories must be a list')
            continue

        for entry in story_list:
            for key in ("id", "title", "genre", "file"):
                if key not in entry:
                    issues.error("index-entry-missing-key",
                                 f'Story entry in {lid} missing key "{key}"')

            # Genre must be a key in genres
            genre = entry.get("genre", "")
            if genre not in genres:
                issues.error("index-bad-genre",
                             f'Story "{entry.get("id", "?")}" genre "{genre}" not in genres')

            # File must exist
            file_path = ROOT / "data" / entry.get("file", "")
            if not file_path.exists():
                issues.error("index-missing-file",
                             f'Story file not found: {entry.get("file", "?")}')

            referenced_files.add(entry.get("file", ""))

    return referenced_files


# ── Orphan detection ──

def detect_orphans(referenced_files, issues):
    """Warn about story files on disk not referenced in index.json (section 3)."""
    count = 0
    if STORIES_DIR.exists():
        for path in sorted(STORIES_DIR.glob("*.json")):
            rel = f"stories/{path.name}"
            if rel not in referenced_files:
                issues.warn("orphan-file", f"{path.name} not referenced in index.json")
                count += 1
    return count


# ── Token validation helpers ──

def validate_token(token, context, issues):
    """Validate a single token's structure. Returns True if it's a word token."""
    text = token.get("text")
    pinyin = token.get("pinyin")
    translation = token.get("translation")

    # Required keys
    for key in ("text", "pinyin", "translation"):
        if key not in token:
            issues.error("token-missing-key", f'{context}: token missing key "{key}"')
            return False

    if not isinstance(text, str) or not text:
        issues.error("token-bad-text", f"{context}: token text must be a non-empty string")
        return False

    if is_punctuation(text):
        # Punctuation: pinyin and translation must both be null
        if pinyin is not None:
            issues.error("punct-has-pinyin",
                         f'{context}: punctuation "{text}" has non-null pinyin')
        if translation is not None:
            issues.error("punct-has-translation",
                         f'{context}: punctuation "{text}" has non-null translation')
        return False
    else:
        # Word token: pinyin and translation must be non-empty strings
        if not isinstance(pinyin, str) or not pinyin:
            issues.error("word-missing-pinyin",
                         f'{context}: word "{text}" has empty or null pinyin')
        if not isinstance(translation, str) or not translation:
            issues.error("word-missing-translation",
                         f'{context}: word "{text}" has empty or null translation')
        return True


# ── Story schema validation ──

def validate_story_schema(story_id, story, index_entry, level_id, issues):
    """Validate a single story file's structure (section 4)."""
    # Required top-level keys
    for key in ("id", "title", "title_segments", "genre", "level", "content"):
        if key not in story:
            issues.error("story-missing-key",
                         f'Missing required key "{key}"')

    # ID format and consistency
    sid = story.get("id", "")
    if not ID_PATTERN.match(sid):
        issues.error("story-bad-id",
                     f'id "{sid}" does not match hsk\\d+-\\w[\\w-]+')
    if sid != index_entry["id"]:
        issues.error("story-id-mismatch",
                     f'id "{sid}" does not match index entry "{index_entry["id"]}"')

    # Level must be a positive int and match filename
    level = story.get("level")
    if not isinstance(level, int) or level < 1:
        issues.error("story-bad-level", f"level must be a positive int, got {level!r}")
    else:
        expected_level = int(re.search(r"\d+", level_id).group())
        if level != expected_level:
            issues.error("story-level-mismatch",
                         f"level {level} does not match {level_id}")

    # Genre must match index
    genre = story.get("genre", "")
    if genre != index_entry.get("genre", ""):
        issues.error("story-genre-mismatch",
                     f'genre "{genre}" does not match index "{index_entry.get("genre", "")}"')

    # Content must be a non-empty list of lists
    content = story.get("content", [])
    if not isinstance(content, list) or len(content) == 0:
        issues.error("story-bad-content", "content must be a non-empty list")
    else:
        for i, para in enumerate(content):
            if not isinstance(para, list):
                issues.error("story-bad-paragraph",
                             f"content[{i}] must be a list, got {type(para).__name__}")

    # Title segments must be a list of tokens
    title_segs = story.get("title_segments", [])
    if not isinstance(title_segs, list):
        issues.error("story-bad-title-segments", "title_segments must be a list")
    else:
        for token in title_segs:
            validate_token(token, "title_segments", issues)

    # Validate all content tokens
    word_count = 0
    unique_words = set()
    if isinstance(content, list):
        for i, para in enumerate(content):
            if not isinstance(para, list):
                continue
            for token in para:
                is_word = validate_token(token, f"para[{i}]", issues)
                if is_word:
                    word_count += 1
                    unique_words.add(token["text"])

    para_count = len(content) if isinstance(content, list) else 0
    return word_count, unique_words, para_count


# ── Lexicon validation ──

def validate_against_lexicon(story_id, story, lexicon, issues):
    """Check tokens against lexicon (section 5). Returns above-level count."""
    level = story.get("level", 0)
    above_level = 0

    def check_token(token):
        nonlocal above_level
        text = token.get("text", "")
        pinyin = token.get("pinyin")
        translation = token.get("translation")

        if pinyin is None:
            return  # punctuation

        if text not in lexicon:
            issues.warn("not-in-lexicon", f'"{text}" not in lexicon')
            return

        entry = lexicon[text]

        # Pinyin mismatch is an error
        if pinyin != entry["pinyin"]:
            issues.error("pinyin-mismatch",
                         f'"{text}": story has "{pinyin}", lexicon has "{entry["pinyin"]}"')

        # Translation not in meanings is a warning
        if translation and translation not in entry.get("meanings", []):
            issues.warn("translation-not-in-meanings",
                        f'"{text}": "{translation}" not in lexicon meanings')

        # Track above-level words
        if isinstance(level, int) and entry.get("level", 0) > level:
            above_level += 1

    # Check title segments
    for token in story.get("title_segments", []):
        check_token(token)

    # Check content
    for para in story.get("content", []):
        if isinstance(para, list):
            for token in para:
                check_token(token)

    return above_level


# ── Reporting ──

def print_story_detail(story_id, word_count, unique_count, para_count,
                       above_level, issues):
    """Print per-story detail block."""
    print(f"\n--- {story_id} ---")
    print(f"  Schema: {'ERRORS' if issues.has_errors else 'OK'}")
    print(f"  Tokens: {word_count} words, {unique_count} unique, {para_count} paragraphs")

    above_pct = (above_level / word_count * 100) if word_count > 0 else 0.0
    print(f"  Above-level: {above_level} ({above_pct:.1f}%)")

    if issues.warnings:
        print(f"  Warnings:")
        for tag, msg in issues.warnings:
            print(f"    [{tag}] {msg}")

    if issues.errors:
        print(f"  Errors:")
        for tag, msg in issues.errors:
            print(f"    [{tag}] {msg}")


def print_cross_story_stats(lexicon, all_story_words, level_map):
    """Print cross-story statistics (section 7)."""
    print(f"\n=== Cross-Story Stats ===")

    # Vocabulary coverage per level
    # Group lexicon words by level
    lexicon_by_level = {}
    for word, entry in lexicon.items():
        lv = entry.get("level", 0)
        if lv not in lexicon_by_level:
            lexicon_by_level[lv] = set()
        lexicon_by_level[lv].add(word)

    # Group story words by story level
    words_used_by_level = {}
    for story_id, words in all_story_words.items():
        lv = level_map.get(story_id, 0)
        if lv not in words_used_by_level:
            words_used_by_level[lv] = set()
        words_used_by_level[lv].update(words)

    for lv in sorted(lexicon_by_level.keys()):
        total = len(lexicon_by_level[lv])
        used = len(words_used_by_level.get(lv, set()) & lexicon_by_level[lv])
        pct = (used / total * 100) if total > 0 else 0.0
        print(f"Level {lv}: {used}/{total} lexicon words used ({pct:.1f}%)")

    # Words appearing in only one story
    word_story_count = {}
    for story_id, words in all_story_words.items():
        for w in words:
            word_story_count[w] = word_story_count.get(w, 0) + 1
    single_story = sum(1 for c in word_story_count.values() if c == 1)
    print(f"Words appearing in only 1 story: {single_story}")


def print_summary(story_rows, total_errors, total_warnings, error_counts, warning_counts):
    """Print the final summary table (section 8)."""
    print(f"\n=== Summary ===")

    # Header
    print(f"{'Story':<45} {'Words':>5}  {'Unique':>6}  {'Above%':>6}  {'Err':>3}  {'Warn':>4}")
    for row in story_rows:
        above_pct = (row["above"] / row["words"] * 100) if row["words"] > 0 else 0.0
        print(f"{row['id']:<45} {row['words']:>5}  {row['unique']:>6}  "
              f"{above_pct:>5.1f}%  {row['errors']:>3}  {row['warnings']:>4}")

    print(f"\nErrors: {total_errors}")
    print(f"Warnings: {total_warnings}")

    if error_counts:
        for tag, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"  {tag}: {count}")
    if warning_counts:
        for tag, count in sorted(warning_counts.items(), key=lambda x: -x[1]):
            print(f"  {tag}: {count}")

    if total_errors == 0:
        print(f"\nResult: PASS")
    else:
        print(f"\nResult: FAIL ({total_errors} error{'s' if total_errors != 1 else ''})")


# ── Main ──

def main():
    parser = argparse.ArgumentParser(
        description="Validate story data against the lexicon.")
    parser.add_argument("--verbose", action="store_true",
                        help="Show full stats for every story")
    args = parser.parse_args()

    print("=== Validating Chinese Graded Reader Data ===\n")
    print("Loading data...")

    lexicon = load_json(LEXICON_FILE)
    index = load_json(INDEX_FILE)

    valid_levels = set()
    for level in index.get("levels", []):
        valid_levels.add(level.get("id", ""))

    print(f"  Lexicon: {len(lexicon)} words")
    print(f"  Index: {len(index.get('levels', []))} levels, "
          f"{sum(len(lv.get('stories', [])) for lv in index.get('levels', []))} stories")

    # Validate index structure
    index_issues = Issues()
    referenced_files = validate_index(index, index_issues)
    if index_issues.has_issues:
        print(f"\nIndex issues:")
        for tag, msg in index_issues.errors:
            print(f"  ERROR [{tag}] {msg}")
        for tag, msg in index_issues.warnings:
            print(f"  WARN  [{tag}] {msg}")

    # Detect orphan files
    orphan_issues = Issues()
    orphan_count = detect_orphans(referenced_files, orphan_issues)
    print(f"  Orphan files: {orphan_count}")
    if orphan_issues.warnings:
        for tag, msg in orphan_issues.warnings:
            print(f"    [{tag}] {msg}")

    # Load all stories
    stories = {}
    for level in index.get("levels", []):
        for entry in level.get("stories", []):
            story_path = ROOT / "data" / entry["file"]
            if story_path.exists():
                stories[entry["id"]] = {
                    "data": load_json(story_path),
                    "index_entry": entry,
                    "level_id": level["id"],
                }

    # Per-story validation
    total_errors = len(index_issues.errors)
    total_warnings = len(index_issues.warnings) + len(orphan_issues.warnings)
    error_counts = {}
    warning_counts = {}
    story_rows = []
    all_story_words = {}  # story_id -> set of unique words
    level_map = {}  # story_id -> int level

    # Count index/orphan issues into tallies
    for tag, _ in index_issues.errors:
        error_counts[tag] = error_counts.get(tag, 0) + 1
    for tag, _ in index_issues.warnings:
        warning_counts[tag] = warning_counts.get(tag, 0) + 1
    for tag, _ in orphan_issues.warnings:
        warning_counts[tag] = warning_counts.get(tag, 0) + 1

    for story_id, info in stories.items():
        story = info["data"]
        index_entry = info["index_entry"]
        level_id = info["level_id"]

        issues = Issues()

        # Schema validation (section 4)
        word_count, unique_words, para_count = validate_story_schema(
            story_id, story, index_entry, level_id, issues)

        # Lexicon validation (section 5)
        above_level = validate_against_lexicon(story_id, story, lexicon, issues)

        # Collect stats
        all_story_words[story_id] = unique_words
        story_level = story.get("level", 0)
        level_map[story_id] = story_level

        # Tally issues
        total_errors += len(issues.errors)
        total_warnings += len(issues.warnings)
        for tag, _ in issues.errors:
            error_counts[tag] = error_counts.get(tag, 0) + 1
        for tag, _ in issues.warnings:
            warning_counts[tag] = warning_counts.get(tag, 0) + 1

        # Print per-story detail
        if args.verbose or issues.has_issues:
            print_story_detail(story_id, word_count, len(unique_words),
                               para_count, above_level, issues)

        story_rows.append({
            "id": story_id,
            "words": word_count,
            "unique": len(unique_words),
            "above": above_level,
            "errors": len(issues.errors),
            "warnings": len(issues.warnings),
        })

    # Cross-story stats (section 7)
    print_cross_story_stats(lexicon, all_story_words, level_map)

    # Summary (section 8)
    print_summary(story_rows, total_errors, total_warnings,
                  error_counts, warning_counts)

    return 1 if total_errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
