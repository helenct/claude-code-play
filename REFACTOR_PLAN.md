# Refactor Plan: Structural Foundation for Scalability

**Created:** February 23, 2026
**Goal:** Shore up the data architecture before adding new content, features, or HSK levels.

## Problems to Solve

### 1. Above-level detection is broken (~22-30% false positive rate)
- `hsk_vocab.js` uses pre-2021 HSK word lists with significant gaps
- Basic words missing from all levels: 他们, 每天, 哪里, 不是
- Words placed too high: 也/问/给 are HSK 2 but appear constantly in HSK 1 stories
- Segmentation mismatch: stories tokenize 说话 as one word, but only 说 is in HSK 1, so 说话 gets flagged — even in the story titled "会说话的书"
- `isAboveLevel()` does exact string matching with no fallback

### 2. No canonical vocabulary source — translations are inconsistent
- Each word's pinyin and translation were written ad-hoc during story creation
- Same word gets different translations: 看 has 10 variants, 说 has 7, 是 has 6
- Same word sometimes has different pinyin: 不是 → "bùshì" / "bú shì"

### 3. Flat story data with no paragraph structure
- All stories are flat arrays of word tokens — no way to represent paragraph breaks
- Will become a readability problem as stories get longer

### 4. Single monolithic data file won't scale
- `data/texts.json` is ~23K lines for 20 stories
- Adding stories means editing one giant file — bad for git diffs, slow to load
- No way to lazy-load individual stories

### 5. Inconsistent story IDs
- HSK 1-2: `hsk1_comedy_reading_dog`, `hsk2_mystery_lunch_thief`
- HSK 3-4: `hsk3-comedy`, `hsk4-scifi`
- Mixed delimiters, HSK 3-4 IDs missing story names

---

## Frequency Data: Foundation for Level Assignment

Rather than relying on the old HSK word lists (which are incomplete and arguable), we ground level assignments in **corpus frequency data** — specifically [SUBTLEX-CH](https://www.ugent.be/pp/experimentele-psychologie/en/research/documents/subtlexch), a word frequency list derived from 33.5 million words of Chinese film/TV subtitles (Cai & Brysbaert, 2010). This is the standard frequency dataset used in psycholinguistic research on Chinese, and subtitle-based corpora are widely considered the best proxy for everyday spoken language.

### What we have

Downloaded to `reference/` (not shipped with the app — used during lexicon building only):

| File | Source | Contents |
|------|--------|----------|
| `SUBTLEX_CH_131210_CE.utf8` | SUBTLEX-CH | 99,121 words with frequency rank, pinyin, part of speech, English translations |
| `SUBTLEX-CH-WF` | SUBTLEX-CH | Same words, frequency counts only (GB18030 encoding) |
| `hanzi_db.csv` | [hanziDB](https://github.com/ruddfawcett/hanziDB.csv) | 9,900 characters with frequency rank, pinyin, HSK level, radical, stroke count (MIT license) |
| `freq_words.csv` | [wuxialearn](https://github.com/wuxialearn/Chinese-English-Frequency-Dictionary) | ~1,400 curated high-frequency words with example sentences |

### Coverage analysis

- **96% of the 823 unique words in our stories** appear in SUBTLEX-CH
- The 34 missing words are mostly compounds of common subwords (第一天, 孩子们, 有点儿, 朋友圈) or proper nouns (普洱茶) — these get manual lexicon entries
- Character frequency data from hanziDB helps grade compound words not in SUBTLEX: if all characters are high-frequency, the compound is likely appropriate for lower levels

### Proposed level bands

Frequency rank drives the *default* level assignment. The bands are:

| Level | SUBTLEX Rank | Cumulative Words | Description |
|-------|-------------|------------------|-------------|
| 1 | 1–150 | ~150 | Beginner — most common function words, pronouns, basic verbs |
| 2 | 151–400 | ~400 | Elementary — everyday nouns, adjectives, common phrases |
| 3 | 401–800 | ~800 | Intermediate — broader vocabulary, some abstract words |
| 4 | 801–1500 | ~1,500 | Upper intermediate — nuanced verbs, formal expressions |
| 5 | 1501–3000 | ~3,000 | Advanced — specialized vocabulary, literary words |
| 6 | 3001–5000 | ~5,000 | Proficient — low-frequency but useful vocabulary |

These bands are starting points. The lexicon stores both the raw frequency rank AND the assigned level, so we can adjust individual words without losing the underlying data.

### Pedagogical overrides

Pure frequency has known issues for language learning:

- **Grammatically complex high-frequency words**: 把 (#40), 被 (#65), 得 (#49) are among the 50 most frequent words but require understanding of advanced grammar patterns. These get bumped to level 2 or 3 despite their frequency.
- **Subtitle artifacts**: 死 (#103), 嘿 (#109), 嗯 (#128), 噢 (#149) are high-frequency because SUBTLEX is based on movie/TV subtitles. Interjections and dramatic vocabulary get reviewed and bumped if not useful for readers.
- **Topic words below their frequency**: Some words that are thematically basic for storytelling (animal names, food, classroom vocabulary) may have lower corpus frequency but are pedagogically appropriate for early levels. These can be pulled down.

Each override is recorded in the lexicon with a `freq_rank` field preserving the original data, so the reasoning is always auditable.

### How character frequency helps

For compound words not in SUBTLEX (like 孩子们, 第一天, 交通工具), we use character-level frequency from hanziDB as a fallback:

- If all characters are in the top 200 by frequency → likely level 1-2
- If all characters are in the top 500 → likely level 2-3
- And so on

This prevents compounds of basic characters from being flagged as "above level" just because the exact compound string isn't in a word list.

---

## Target Architecture

```
data/
├── lexicon.json              # Canonical vocabulary: pinyin, level, freq rank, meanings
├── index.json                # Story manifest: id, title, level, genre, filename
└── stories/
    ├── hsk1-scifi-talking-book.json
    ├── hsk1-historical-poets-tea.json
    ├── ...
    └── hsk4-philosophical-park-observer.json

reference/                    # NOT shipped with app — used during lexicon building
├── SUBTLEX_CH_131210_CE.utf8
├── SUBTLEX-CH-WF
├── hanzi_db.csv
└── freq_words.csv

scripts/
├── build-lexicon.py          # Generates lexicon.json from stories + frequency data
└── validate.js               # Checks stories against lexicon
```

### Lexicon (`data/lexicon.json`)

Single source of truth for every word used across all stories.

```json
{
  "说话": {
    "pinyin": "shuōhuà",
    "level": 1,
    "freq_rank": 202,
    "pos": "v",
    "meanings": ["to speak", "to talk"]
  },
  "他们": {
    "pinyin": "tāmen",
    "level": 1,
    "freq_rank": 34,
    "pos": "r",
    "meanings": ["they", "them"]
  },
  "看": {
    "pinyin": "kàn",
    "level": 1,
    "freq_rank": 50,
    "pos": "v",
    "meanings": ["to look", "to read", "to watch", "to see"]
  },
  "普洱茶": {
    "pinyin": "pǔěrchá",
    "level": 4,
    "freq_rank": null,
    "pos": "n",
    "meanings": ["Pu'er tea"]
  }
}
```

**Fields:**
- `pinyin` — canonical romanization with tone marks (one form per word)
- `level` — our assigned level (1-6), informed by frequency + pedagogical judgment
- `freq_rank` — SUBTLEX-CH rank, or `null` for words not in the corpus (preserves the underlying data)
- `pos` — dominant part of speech from SUBTLEX (v, n, r, a, d, p, etc.), or manually assigned
- `meanings` — list of valid English translations

**What the lexicon owns:** pinyin, level, frequency data, part of speech, list of valid meanings.

**What the lexicon does NOT own:** which meaning a word has in a specific sentence — that stays in the story file.

**Levels are our own grading**, informed by SUBTLEX frequency as the primary signal, with pedagogical overrides. This lets us extend cleanly to levels 5-6+ by expanding the lexicon from SUBTLEX data (the corpus has 99K words — far more than we'll ever need).

### Story Index (`data/index.json`)

Lightweight manifest loaded on startup. The app uses this to build the sidebar, then fetches individual stories on demand.

```json
{
  "levels": [
    {
      "id": "hsk1",
      "name": "HSK 1",
      "stories": [
        {
          "id": "hsk1-scifi-talking-book",
          "title": "会说话的书",
          "genre": "Sci-Fi",
          "file": "stories/hsk1-scifi-talking-book.json"
        }
      ]
    }
  ]
}
```

### Individual Story Files (`data/stories/*.json`)

Each story is its own file. Content is an array of paragraphs, each an array of word tokens. Stories carry their own contextual translations (since the same word may mean different things in different sentences). Pinyin comes from the story file too (for display), but can be validated against the lexicon.

```json
{
  "id": "hsk1-scifi-talking-book",
  "title": "会说话的书",
  "title_segments": [
    {"text": "会", "pinyin": "huì", "translation": "can"},
    {"text": "说话", "pinyin": "shuōhuà", "translation": "speak"},
    {"text": "的", "pinyin": "de", "translation": "(particle)"},
    {"text": "书", "pinyin": "shū", "translation": "book"}
  ],
  "genre": "Sci-Fi",
  "level": 1,
  "content": [
    [
      {"text": "我", "pinyin": "wǒ", "translation": "I"},
      {"text": "是", "pinyin": "shì", "translation": "am"},
      {"text": "学生", "pinyin": "xuésheng", "translation": "student"},
      {"text": "。", "pinyin": null, "translation": null}
    ],
    [
      {"text": "今天", "pinyin": "jīntiān", "translation": "today"},
      {"text": "我", "pinyin": "wǒ", "translation": "I"},
      {"text": "在", "pinyin": "zài", "translation": "at"},
      {"text": "学校", "pinyin": "xuéxiào", "translation": "school"},
      {"text": "。", "pinyin": null, "translation": null}
    ]
  ]
}
```

**Key change:** `content` is now an array of arrays (paragraphs), not a flat array. The app renders a visual break between paragraphs.

### Above-Level Detection

Replace the hardcoded Sets in `hsk_vocab.js` with logic that reads from the lexicon:

```javascript
// Load lexicon once
let LEXICON = null;

async function loadLexicon() {
  const response = await fetch('data/lexicon.json');
  LEXICON = await response.json();
}

function isAboveLevel(word, readerLevel) {
  if (!LEXICON || !readerLevel) return false;
  const entry = LEXICON[word];
  if (entry) return entry.level > readerLevel;
  // Word not in lexicon at all — flag it (and log for review)
  return true;
}
```

No more maintaining parallel vocab Sets. Add or fix a word in the lexicon and it's immediately reflected everywhere.

---

## Implementation Steps

### Phase 1: Build the Lexicon

1. **Extract every unique word** from all 20 stories in `texts.json`
2. **Cross-reference with SUBTLEX-CH** to get frequency rank, pinyin, part of speech, and English translations for each word
3. **Assign levels** using the frequency bands above as defaults, then apply pedagogical overrides (bump grammatically complex words up, pull thematically basic words down)
4. **Handle words not in SUBTLEX** (~34 words): use character-level frequency from hanziDB to estimate level, add manual pinyin and translations
5. **Deduplicate translations**: for each word, merge all translations seen across stories into a clean meanings list
6. **Resolve pinyin inconsistencies**: pick the canonical SUBTLEX pinyin, adjusted for tone sandhi where appropriate
7. **Write `data/lexicon.json`** and the `scripts/build-lexicon.py` script that generates it (so the process is repeatable when adding new words)

### Phase 2: Split Stories into Individual Files

1. **Normalize all story IDs** to `hsk{N}-{genre}-{slug}` format
2. **Split `texts.json`** into one file per story under `data/stories/`
3. **Add paragraph breaks** to each story's content (convert flat array to array-of-arrays, using sentence-ending punctuation and narrative flow as paragraph boundaries)
4. **Generate `data/index.json`** manifest from the story metadata
5. **Validate** every word token in every story against the lexicon — flag any words not in the lexicon and add them

### Phase 3: Update the App

1. **Replace `hsk_vocab.js`** — load lexicon from JSON instead of hardcoded Sets, update `isAboveLevel()` to use it
2. **Update `app.js` data loading** — load `index.json` on startup, fetch individual story files on demand (when user selects a story)
3. **Update `renderWords()`** to handle paragraph structure — render paragraph breaks between arrays
4. **Update `index.html`** to remove the `<script src="hsk_vocab.js">` tag
5. **Keep `styles.css` and theme unchanged** — no visual changes in this phase

### Phase 4: Add Validation Script

1. **Create `scripts/validate.js`** (Node.js script, run locally or in CI) that:
   - Loads the lexicon and all story files
   - Checks every word token in every story exists in the lexicon
   - Flags pinyin mismatches between story and lexicon
   - Flags translations not in the lexicon's meanings list (warning, not error — context-dependent translations are OK)
   - Reports story-level stats: word count, unique words, above-level word percentage
   - Exits with error code if any hard failures (unknown words, missing files)
2. **Document how to run it** in the README

---

## Design Decisions and Rationale

### Why SUBTLEX-CH for frequency data?
Subtitle-based corpora are the gold standard for modeling everyday language exposure. SUBTLEX-CH is based on 6,243 Chinese films/TV shows (33.5M word tokens) and is the most widely used frequency list in Chinese psycholinguistics. It correlates better with word recognition performance than written-corpus frequencies. It also comes with pinyin, part of speech, and English translations — reducing manual work.

### Why not just use SUBTLEX rankings directly as levels?
Pure frequency ranking has pedagogical problems. 把 (rank #40) requires understanding of the disposal construction. 被 (#65) requires passive voice. 死 (#103) is high-frequency from movie dramas but not a priority for beginners. Frequency is the *starting point* for level assignment, not the final word. The lexicon stores both `freq_rank` (the data) and `level` (the judgment), keeping them separable.

### Why include character frequency data too?
SUBTLEX-CH is a *word* frequency list. Some perfectly natural compound words aren't in it (孩子们, 第一天, 有点儿). Character-level frequency from hanziDB lets us grade these compounds sensibly: if every character in 孩子们 is in the top 100 by frequency, the compound is clearly beginner-level even though it's not in the word list. This is especially useful for story generation, where an LLM might produce valid compounds that aren't in any word list.

### Why keep translations in story files (not just the lexicon)?
Context matters. 看 means "to read" when looking at a book and "to watch" when watching TV. The story file carries the contextual translation for display. The lexicon's meanings list is for validation ("is this a known meaning of this word?") and for story generation ("what are the possible translations?").

### Why our own levels instead of official HSK?
The pre-2021 lists have gaps (他们 missing from all levels). The post-2021 lists restructured into 7-9 levels. Rather than chasing a moving standard, we maintain our own grading with frequency data as the empirical foundation. This also means extending to levels 5-6+ is just expanding the lexicon from SUBTLEX data (which has 99K words available).

### Why array-of-arrays for paragraphs instead of marker tokens?
A marker token like `{"text": "\n", ...}` works but is fragile — easy to accidentally strip, harder to map to semantic structure (paragraph N). Nested arrays make paragraph boundaries explicit in the data structure. They're also easier to work with for future features (per-paragraph images, per-paragraph audio, collapsible paragraphs).

### Why individual story files instead of one file per level?
Individual files give the best granularity: lazy loading (fetch one story at a time), clean git diffs (changing a story only touches one file), easy to add/remove stories without editing a shared file. One file per level would be a middle ground but doesn't buy much over individual files.

### Why a validation script rather than runtime checks?
Runtime validation slows down the app and can't prevent bad data from being deployed. A script that runs before deployment catches problems early. It also produces useful reports (vocabulary coverage, consistency stats) that help with content planning.

---

## Future-Proofing Notes

### Adding new stories
1. Create a new story file in `data/stories/`
2. Run `scripts/build-lexicon.py` to add any new words (or add them manually)
3. Add the story to `data/index.json`
4. Run the validation script

### Adding levels 5-6+
1. Expand the lexicon from SUBTLEX-CH data for ranks 1501-5000+ (the data is already downloaded in `reference/`)
2. Add new level entries to `data/index.json`
3. The app and detection logic handle arbitrary levels — no code changes needed

### Automated story generation
A generation function would:
1. Take the lexicon + target level as input
2. Know which words are available (all words at or below the target level)
3. Use frequency rank to prefer common words and introduce rarer ones gradually
4. Output a story file conforming to the schema above
5. The validation script verifies the output before it's added

The lexicon acts as the contract between the generator and the reader app. The frequency data in the lexicon means the generator doesn't just know *which* words are allowed — it knows which are common vs. rare within a level, enabling more natural-sounding text.

---

## Files Changed

| File | Action |
|------|--------|
| `data/lexicon.json` | **New** — canonical vocabulary with frequency data |
| `data/index.json` | **New** — story manifest |
| `data/stories/*.json` | **New** — 20 individual story files |
| `data/texts.json` | **Delete** after migration |
| `hsk_vocab.js` | **Delete** — replaced by lexicon |
| `app.js` | **Rewrite** data loading, add lazy fetch, handle paragraphs |
| `index.html` | **Edit** — remove hsk_vocab.js script tag |
| `styles.css` | **Edit** — add paragraph spacing (minor) |
| `scripts/build-lexicon.py` | **New** — generates lexicon from stories + frequency data |
| `scripts/validate.js` | **New** — checks stories against lexicon |
| `reference/` | **New directory** — frequency data files (git-ignored or kept for reproducibility) |
| `PROJECT_STATUS.md` | **Update** to reflect new architecture |
