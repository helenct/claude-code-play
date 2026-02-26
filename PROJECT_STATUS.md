# Chinese Graded Reader - Project Status
**Last Updated:** February 24, 2026

## Current State

All 20 stories are integrated into the app. The UI uses the **Jade Split** theme — a persistent two-pane sidebar layout with a dark teal sidebar and light mint reading pane.

**Live site:** https://helenct.github.io/claude-code-play/
**Active branch:** `refactor-plan` — structural refactor in progress (Phases 1-3 complete, not yet merged to main)

### Navigation Model
- Dark teal sidebar: logo, HSK level nav (vertical stack), scrollable story list
- Light mint main pane: story title, genre badge, instruction text, word-segmented content with paragraph breaks
- Selecting a level populates the story list and auto-selects the first story
- Selecting a story fetches its file on demand and renders it in the reading pane

### Known Issue
- 会说话的书 (HSK 1, Sci-Fi) is incomplete (~120 word entries vs ~200+ for other stories). The full version was never finished during story creation.

### Recent Changes (main branch)
- Readability QoL improvements: bumped small font sizes (sidebar genre tags, story list heading, reading instruction, tooltips), increased mobile text sizes, added `max-width: 720px` to reading content

## Refactor In Progress

See `REFACTOR_PLAN.md` for the full plan. Summary of what's done and what's next:

### Phase 1: Build Lexicon — DONE
- Created `data/lexicon.json` (828 words) with canonical pinyin, level 1-6 grading, frequency rank, POS, and meanings
- Levels are based on SUBTLEX-CH corpus frequency (99K words from 33.5M Chinese subtitle tokens) with 87 pedagogical overrides
- Frequency reference data in `reference/` (gitignored): SUBTLEX-CH word frequency, hanziDB character frequency
- Build script: `scripts/build-lexicon.py` — regenerate the lexicon by running `python3 scripts/build-lexicon.py`
- Above-level detection false positive rate dropped from ~22-30% to ~14% for level 1 stories

### Phase 2: Split Stories — DONE
- Split monolithic `data/texts.json` into 20 individual files under `data/stories/`
- Normalized all story IDs to consistent `hsk{N}-{genre}-{slug}` format
- Normalized genre casing (`Sci-fi` → `Sci-Fi`)
- Added paragraph breaks (flat array → array of arrays) with manual break points at narrative boundaries
- Handled orphaned closing quotes at paragraph boundaries (both curly and straight quote styles)
- Generated `data/index.json` manifest with genre display data
- Validated all 4,492 tokens against the lexicon (100% coverage)
- Migration script: `scripts/split-stories.py`

### Phase 3: Update the App — DONE
- App now loads `index.json` + `lexicon.json` on startup (instead of `texts.json`)
- Individual story files fetched on demand with caching (instead of loading all stories upfront)
- Above-level detection uses lexicon levels (instead of hardcoded HSK vocab sets)
- Paragraph breaks rendered in reading pane
- Genre badge data moved from `hsk_vocab.js` to `index.json`
- Removed `hsk_vocab.js` dependency
- **Not yet tested in browser** — needs manual verification

### Phase 4: Add Validation Script — TODO
- Script to check all stories against lexicon, flag mismatches

## Stories (20 total)

Each story is an individual JSON file in `data/stories/`. Content is structured as paragraphs (array of arrays of word tokens).

### HSK 1 (5 stories)
- 会说话的书 (The Talking Book) - Sci-Fi **(incomplete)**
- 诗人的茶 (The Poet's Tea) - Historical Fiction
- 我的影子朋友 (My Shadow Friend) - Magical Realism
- 读书的狗 (The Reading Dog) - Comedy
- 新邻居 (New Neighbors) - Slice of Life

### HSK 2 (5 stories)
- 聪明的闹钟 (The Smart Alarm) - Sci-Fi
- 爷爷的地图 (Grandfather's Map) - Historical Fiction
- 魔法厨房 (The Magic Kitchen) - Magical Realism
- 上错了课 (Wrong Class) - Comedy
- 午饭小偷 (Lunch Thief) - Mystery

### HSK 3 (5 stories)
- 标签眼镜 (The Label Glasses) - Sci-Fi
- 进城 - 1985 (Moving to the City - 1985) - Historical Fiction
- 诚实的自行车 (The Honest Bicycle) - Magical Realism
- 错误的手机 (Wrong Phone) - Comedy
- 阳台花园 (The Balcony Garden) - Drama

### HSK 4 (5 stories)
- 明天的茶 (Tea from Tomorrow) - Sci-Fi
- 书法家的选择 (The Calligrapher's Choice) - Historical Fiction
- 记忆茶馆 (The Memory Teahouse) - Magical Realism
- 奶奶玩网络 (Grandma Goes Digital) - Comedy
- 公园观察者 (The Park Observer) - Philosophical

## File Structure
```
claude-code-play/
├── index.html              (Google Fonts + app shell)
├── app.js                  (loads index/lexicon, fetches stories on demand)
├── styles.css              (Jade Split theme + paragraph spacing)
├── data/
│   ├── index.json          (story manifest + genre display data)
│   ├── lexicon.json        (canonical vocabulary, 828 words)
│   └── stories/            (20 individual story files)
│       ├── hsk1-scifi-talking-book.json
│       ├── hsk1-historical-poets-tea.json
│       ├── ...
│       └── hsk4-philosophical-park-observer.json
├── scripts/
│   ├── build-lexicon.py    (generates lexicon from stories + frequency data)
│   └── split-stories.py    (splits texts.json into individual story files)
├── reference/              (gitignored — SUBTLEX-CH + hanziDB frequency data)
├── PROJECT_STATUS.md
├── REFACTOR_PLAN.md
├── README.md
├── IMPLEMENTATION_GUIDE.md (story creation reference)
├── STORIES_SUMMARY.md      (story outlines)
└── TEST_INSTRUCTIONS.md
```

## Data Format

### Story files (`data/stories/*.json`)
```json
{
  "id": "hsk1-scifi-talking-book",
  "title": "会说话的书",
  "title_segments": [{"text": "会", "pinyin": "huì", "translation": "can"}, ...],
  "genre": "Sci-Fi",
  "level": 1,
  "content": [
    [{"text": "我", "pinyin": "wǒ", "translation": "I"}, ...],
    [{"text": "书", "pinyin": "shū", "translation": "book"}, ...]
  ]
}
```
Content is an array of paragraphs, each an array of word tokens.
Punctuation: `{"text": "。", "pinyin": null, "translation": null}`

## Potential Next Steps
- **Browser-test the refactor branch** — Phases 1-3 are code-complete but untested in browser
- Phase 4: Add validation script
- Complete the 会说话的书 story
- Add touch support for mobile (tap instead of hover for tooltips)
- Add progress tracking / bookmarking
