# Chinese Graded Reader - Project Status
**Last Updated:** February 23, 2026

## Current State

All 20 stories are integrated into the app. The UI uses the **Jade Split** theme — a persistent two-pane sidebar layout with a dark teal sidebar and light mint reading pane.

**Live site:** https://helenct.github.io/claude-code-play/
**Active branch:** `refactor-plan` — structural refactor in progress (not yet merged to main)

### Navigation Model
- Dark teal sidebar: logo, HSK level nav (vertical stack), scrollable story list
- Light mint main pane: story title, genre badge, instruction text, word-segmented content
- Selecting a level populates the story list and auto-selects the first story
- Selecting a story renders it in the reading pane

### Known Issue
- 会说话的书 (HSK 1, Sci-Fi) is incomplete (~120 word entries vs ~200+ for other stories). The full version was never finished during story creation.

## Refactor In Progress

See `REFACTOR_PLAN.md` for the full plan. Summary of what's done and what's next:

### Phase 1: Build Lexicon — DONE
- Created `data/lexicon.json` (828 words) with canonical pinyin, level 1-6 grading, frequency rank, POS, and meanings
- Levels are based on SUBTLEX-CH corpus frequency (99K words from 33.5M Chinese subtitle tokens) with 87 pedagogical overrides
- Frequency reference data in `reference/` (gitignored): SUBTLEX-CH word frequency, hanziDB character frequency
- Build script: `scripts/build-lexicon.py` — regenerate the lexicon by running `python3 scripts/build-lexicon.py`
- Above-level detection false positive rate dropped from ~22-30% to ~14% for level 1 stories

### Phase 2: Split Stories — TODO (next)
- Split `data/texts.json` into individual files under `data/stories/`
- Normalize story IDs to consistent `hsk{N}-{genre}-{slug}` format
- Add paragraph breaks (flat array → array of arrays)
- Generate `data/index.json` manifest

### Phase 3: Update the App — TODO
- Load lexicon from JSON instead of hardcoded `hsk_vocab.js`
- Lazy-load individual story files on demand
- Render paragraph breaks in reading pane

### Phase 4: Add Validation Script — TODO
- Script to check all stories against lexicon, flag mismatches

## Stories (20 total)

All story data lives in `data/texts.json`.

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
├── app.js                  (sidebar/pane navigation logic)
├── styles.css              (Jade Split theme)
├── hsk_vocab.js            (HSK 1-4 vocab sets — will be replaced by lexicon in Phase 3)
├── data/
│   ├── texts.json          (all 20 stories — will be split in Phase 2)
│   └── lexicon.json        (NEW: canonical vocabulary, 828 words)
├── scripts/
│   └── build-lexicon.py    (NEW: generates lexicon from stories + frequency data)
├── reference/              (gitignored — SUBTLEX-CH + hanziDB frequency data)
├── PROJECT_STATUS.md
├── REFACTOR_PLAN.md        (NEW: full refactor plan with rationale)
├── README.md
├── IMPLEMENTATION_GUIDE.md (story creation reference)
├── STORIES_SUMMARY.md      (story outlines)
└── TEST_INSTRUCTIONS.md
```

## Data Format
Each word entry: `{"text": "你好", "pinyin": "nǐ hǎo", "translation": "hello"}`
Punctuation: `{"text": "。", "pinyin": null, "translation": null}`

## Potential Next Steps
- Complete the 会说话的书 story
- Add touch support for mobile (tap instead of hover for tooltips)
- Add progress tracking / bookmarking
