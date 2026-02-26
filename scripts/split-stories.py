#!/usr/bin/env python3
"""
Phase 2 migration: Split texts.json into individual story files.

Reads data/texts.json and produces:
  - data/stories/<id>.json   (one per story, with paragraph structure)
  - data/index.json           (lightweight manifest for app startup)

Also validates every word token against data/lexicon.json.
"""

import json
import os
import sys

# ── ID normalization map ──
# Old ID → new hsk{N}-{genre}-{slug} format
ID_MAP = {
    # HSK 1
    "hsk1-scifi":                        "hsk1-scifi-talking-book",
    "hsk1_historical_poet_tea":          "hsk1-historical-poets-tea",
    "hsk1_magical_shadow_friend":        "hsk1-magical-shadow-friend",
    "hsk1_comedy_reading_dog":           "hsk1-comedy-reading-dog",
    "hsk1_slice_of_life_new_neighbors":  "hsk1-slice-of-life-new-neighbors",
    # HSK 2
    "hsk2_scifi_smart_alarm":            "hsk2-scifi-smart-alarm",
    "hsk2_historical_grandfather_map":   "hsk2-historical-grandfathers-map",
    "hsk2_magical_magic_kitchen":        "hsk2-magical-magic-kitchen",
    "hsk2_comedy_wrong_class":           "hsk2-comedy-wrong-class",
    "hsk2_mystery_lunch_thief":          "hsk2-mystery-lunch-thief",
    # HSK 3
    "hsk3-scifi":       "hsk3-scifi-label-glasses",
    "hsk3-historical":  "hsk3-historical-moving-to-city",
    "hsk3-magical":     "hsk3-magical-honest-bicycle",
    "hsk3-comedy":      "hsk3-comedy-wrong-phone",
    "hsk3-drama":       "hsk3-drama-balcony-garden",
    # HSK 4
    "hsk4-scifi":         "hsk4-scifi-tomorrows-tea",
    "hsk4-historical":    "hsk4-historical-calligraphers-choice",
    "hsk4-magical":       "hsk4-magical-memory-teahouse",
    "hsk4-comedy":        "hsk4-comedy-grandma-goes-digital",
    "hsk4-philosophical": "hsk4-philosophical-park-observer",
}

# Genre normalization (fix casing inconsistencies)
GENRE_MAP = {
    "Sci-fi": "Sci-Fi",
}

SENTENCE_ENDERS = frozenset("。！？!?")

# Closing punctuation that should never start a paragraph — move to previous.
CLOSING_MARKS = frozenset("\u201d\uff09\u300b\u3011)")  # " ） 》 】 )

# ── Manual paragraph breaks ──
# Maps new story ID → list of 1-based sentence numbers to break AFTER.
# These were chosen by reading each story and finding natural narrative breaks
# (scene changes, time jumps, dialogue boundaries, topic shifts).
MANUAL_BREAKS = {
    # HSK 1 — many short sentences, dialogue-heavy
    "hsk1-scifi-talking-book":          [5, 10],
    "hsk1-historical-poets-tea":        [5, 12, 20, 30, 39],
    "hsk1-magical-shadow-friend":       [5, 11, 17, 24, 31],
    "hsk1-comedy-reading-dog":          [3, 11, 16, 23, 32],
    "hsk1-slice-of-life-new-neighbors": [4, 12, 22, 31, 38],
    # HSK 2 — longer sentences, still some dialogue
    "hsk2-scifi-smart-alarm":           [10, 19, 28],
    "hsk2-historical-grandfathers-map": [5, 14, 19],
    "hsk2-magical-magic-kitchen":       [3, 8, 14, 22],
    "hsk2-comedy-wrong-class":          [8, 15, 24, 31],
    "hsk2-mystery-lunch-thief":         [5, 11, 16, 23, 28],
    # HSK 3 — narrative prose, fewer sentences
    "hsk3-scifi-label-glasses":         [4, 8],
    "hsk3-historical-moving-to-city":   [5, 9, 13],
    "hsk3-magical-honest-bicycle":      [5, 11],
    "hsk3-comedy-wrong-phone":          [3, 11, 17],
    "hsk3-drama-balcony-garden":        [5, 10, 16],
    # HSK 4 — longer narrative, some embedded quotes
    "hsk4-scifi-tomorrows-tea":                [5, 11],
    "hsk4-historical-calligraphers-choice":    [4, 10, 13],
    "hsk4-magical-memory-teahouse":            [5, 10, 16],
    "hsk4-comedy-grandma-goes-digital":        [5, 12],
    "hsk4-philosophical-park-observer":        [5, 11, 15],
}


def find_sentence_boundaries(tokens):
    """Return list of token indices where sentences end (the punctuation position)."""
    return [i for i, t in enumerate(tokens) if t["text"] in SENTENCE_ENDERS]


def count_unclosed_quotes(tokens):
    """Count unclosed opening quotes in a token list.

    The corpus uses a mix of \u201c (left curly) and U+0022 (straight ")
    for both opening and closing. For straight quotes, we use a toggle:
    at depth 0 it opens, at depth > 0 it closes.
    """
    depth = 0
    for t in tokens:
        ch = t["text"]
        if len(ch) != 1:
            continue
        if ch == "\u201c":
            depth += 1
        elif ch == "\u201d":
            depth = max(0, depth - 1)
        elif ch == '"':
            if depth > 0:
                depth -= 1  # closing
            else:
                depth += 1  # opening
    return depth


def fix_orphan_quotes(paragraphs):
    """Move orphaned closing quote marks from the start of a paragraph
    to the end of the previous paragraph.

    In Chinese typesetting, a closing " often appears as a separate token
    right after a sentence-ending period inside quotes. When a paragraph
    boundary falls at that period, the " gets stranded at the start of
    the next paragraph. This fixes that.

    Handles both curly quotes (\u201d) and straight quotes (U+0022) used
    as closing marks. For straight quotes, checks whether the previous
    paragraph has an unclosed opening quote to disambiguate.
    """
    for i in range(1, len(paragraphs)):
        if not paragraphs[i]:
            continue
        first = paragraphs[i][0]
        if first["pinyin"] is not None:
            continue
        ch = first["text"]
        # Unambiguous closing marks
        if ch in CLOSING_MARKS:
            paragraphs[i - 1].append(paragraphs[i].pop(0))
        # Straight quote: closing only if previous paragraph has unclosed opening
        elif ch == '"' and count_unclosed_quotes(paragraphs[i - 1]) > 0:
            paragraphs[i - 1].append(paragraphs[i].pop(0))
    # Remove any paragraphs that became empty
    return [p for p in paragraphs if p]


def split_into_paragraphs(tokens, new_id):
    """Split a flat token list into paragraphs using manual break points.

    Break points are specified as 1-based sentence numbers in MANUAL_BREAKS.
    "Break after sentence N" means the paragraph ends after the Nth sentence.
    """
    sentence_ends = find_sentence_boundaries(tokens)
    num_sentences = len(sentence_ends)

    if num_sentences <= 2:
        return [tokens]

    breaks_after = MANUAL_BREAKS.get(new_id)
    if not breaks_after:
        print(f"    WARNING: No manual breaks for {new_id}, using single paragraph")
        return [tokens]

    # Validate break points
    for b in breaks_after:
        if b < 1 or b > num_sentences:
            print(f"    WARNING: Break point {b} out of range (1-{num_sentences}) for {new_id}")

    # Convert 1-based sentence numbers to token-index split points
    paragraphs = []
    start = 0
    for sent_num in breaks_after:
        if sent_num > num_sentences:
            continue
        end = sentence_ends[sent_num - 1] + 1  # token index after the sentence-ending punct
        if end > start:
            paragraphs.append(tokens[start:end])
            start = end

    # Last paragraph: remaining tokens
    if start < len(tokens):
        paragraphs.append(tokens[start:])

    # Fix orphaned closing quotes at paragraph boundaries
    paragraphs = fix_orphan_quotes(paragraphs)

    return paragraphs


def get_paragraph_preview(paragraph, max_chars=60):
    """Return the first few characters of a paragraph for review."""
    text = "".join(t["text"] for t in paragraph)
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def normalize_genre(genre):
    return GENRE_MAP.get(genre, genre)


def get_level_number(level_id):
    return int(level_id.replace("hsk", ""))


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load source data
    with open(os.path.join(base_dir, "data", "texts.json")) as f:
        data = json.load(f)

    # Load lexicon for validation
    with open(os.path.join(base_dir, "data", "lexicon.json")) as f:
        lexicon = json.load(f)

    # Create stories directory
    stories_dir = os.path.join(base_dir, "data", "stories")
    os.makedirs(stories_dir, exist_ok=True)

    # Build index and story files
    index = {"levels": []}
    total_stories = 0
    total_tokens = 0
    missing_words = {}  # word → list of story IDs where it appears

    for level in data["levels"]:
        level_id = level["id"]
        level_name = level["name"]
        level_num = get_level_number(level_id)

        level_entry = {
            "id": level_id,
            "name": level_name,
            "stories": [],
        }

        for story in level["stories"]:
            old_id = story["id"]
            new_id = ID_MAP.get(old_id)
            if not new_id:
                print(f"  WARNING: No ID mapping for '{old_id}', skipping")
                continue

            genre = normalize_genre(story["genre"])
            title = story["title"]
            title_segments = story.get("title_segments", [])
            content = story["content"]

            # Split into paragraphs
            paragraphs = split_into_paragraphs(content, new_id)

            # Validate tokens against lexicon
            for token in content:
                word = token["text"]
                if token["pinyin"] is None:
                    continue  # punctuation
                if word not in lexicon:
                    if word not in missing_words:
                        missing_words[word] = []
                    missing_words[word].append(new_id)

            # Build story file
            story_data = {
                "id": new_id,
                "title": title,
                "title_segments": title_segments,
                "genre": genre,
                "level": level_num,
                "content": paragraphs,
            }

            # Write story file
            story_path = os.path.join(stories_dir, f"{new_id}.json")
            with open(story_path, "w", encoding="utf-8") as f:
                json.dump(story_data, f, ensure_ascii=False, indent=2)

            # Add to index
            level_entry["stories"].append({
                "id": new_id,
                "title": title,
                "genre": genre,
                "file": f"stories/{new_id}.json",
            })

            # Stats
            total_stories += 1
            total_tokens += len(content)

            # Print paragraph preview
            num_sents = len(find_sentence_boundaries(content))
            print(f"\n  {new_id}  ({num_sents} sentences → {len(paragraphs)} paragraphs)")
            for j, para in enumerate(paragraphs):
                para_sents = sum(1 for t in para if t["text"] in SENTENCE_ENDERS)
                preview = get_paragraph_preview(para)
                print(f"    ¶{j+1} ({para_sents} sents): {preview}")

        index["levels"].append(level_entry)

    # Write index.json
    index_path = os.path.join(base_dir, "data", "index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # ── Summary ──
    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE")
    print("=" * 60)
    print(f"Stories written: {total_stories}")
    print(f"Total tokens:    {total_tokens}")
    print(f"Index written:   data/index.json")
    print(f"Stories dir:     data/stories/")

    if missing_words:
        print(f"\nLEXICON VALIDATION: {len(missing_words)} words not in lexicon:")
        for word, stories in sorted(missing_words.items()):
            print(f"  '{word}' — in {', '.join(stories)}")
    else:
        print("\nLEXICON VALIDATION: All words found in lexicon ✓")

    return 0 if not missing_words else 1


if __name__ == "__main__":
    sys.exit(main())
