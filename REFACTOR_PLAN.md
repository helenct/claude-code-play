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

## Target Architecture

```
data/
├── lexicon.json              # Canonical vocabulary: pinyin, HSK level, meanings
├── index.json                # Story manifest: id, title, level, genre, filename
└── stories/
    ├── hsk1-scifi-talking-book.json
    ├── hsk1-historical-poets-tea.json
    ├── ...
    └── hsk4-philosophical-park-observer.json
```

### Lexicon (`data/lexicon.json`)

Single source of truth for every word used across all stories.

```json
{
  "说话": {
    "pinyin": "shuōhuà",
    "level": 2,
    "meanings": ["to speak", "to talk"]
  },
  "他们": {
    "pinyin": "tāmen",
    "level": 1,
    "meanings": ["they", "them"]
  },
  "看": {
    "pinyin": "kàn",
    "level": 1,
    "meanings": ["to look", "to read", "to watch", "to see"]
  }
}
```

**What the lexicon owns:** pinyin (one canonical form per word), HSK level assignment, list of valid meanings.

**What the lexicon does NOT own:** which meaning a word has in a specific sentence — that stays in the story file.

**HSK levels are our own grading**, informed by but not slavishly following any one official standard. This lets us fix obvious problems (他们 should be level 1) and extend cleanly to HSK 5-6+ without being locked to a standard that might change again.

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
2. **Deduplicate** and pick canonical pinyin for each word (resolve inconsistencies like "bùshì" vs "bú shì")
3. **Assign HSK levels** — start from the existing `hsk_vocab.js` Sets, then fix obvious misplacements (add 他们/每天/哪里 to level 1, etc.)
4. **List valid meanings** for each word (union of all translations seen across stories, cleaned up)
5. **Write out `data/lexicon.json`**

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

### Why keep translations in story files (not just the lexicon)?
Context matters. 看 means "to read" when looking at a book and "to watch" when watching TV. The story file carries the contextual translation for display. The lexicon's meanings list is for validation ("is this a known meaning of this word?") and for story generation ("what are the possible translations?").

### Why not use the official HSK lists directly?
The pre-2021 lists have gaps (他们 missing from all levels). The post-2021 lists restructured into 7-9 levels. Rather than chasing a moving standard, we maintain our own grading informed by multiple sources. This also lets us extend to HSK 5-6+ on our own terms.

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
2. Add any new words to `data/lexicon.json`
3. Add the story to `data/index.json`
4. Run the validation script

### Adding HSK 5-6+
1. Add new words to the lexicon with `"level": 5` or `"level": 6`
2. Add new level entries to `data/index.json`
3. The app and detection logic handle arbitrary levels — no code changes needed

### Automated story generation
A generation function would:
1. Take the lexicon + target HSK level as input
2. Know which words are available (all words at or below the target level)
3. Output a story file conforming to the schema above
4. The validation script verifies the output before it's added

The lexicon acts as the contract between the generator and the reader app.

---

## Files Changed

| File | Action |
|------|--------|
| `data/lexicon.json` | **New** — canonical vocabulary |
| `data/index.json` | **New** — story manifest |
| `data/stories/*.json` | **New** — 20 individual story files |
| `data/texts.json` | **Delete** after migration |
| `hsk_vocab.js` | **Delete** — replaced by lexicon |
| `app.js` | **Rewrite** data loading, add lazy fetch, handle paragraphs |
| `index.html` | **Edit** — remove hsk_vocab.js script tag |
| `styles.css` | **Edit** — add paragraph spacing (minor) |
| `scripts/validate.js` | **New** — validation script |
| `PROJECT_STATUS.md` | **Update** to reflect new architecture |
