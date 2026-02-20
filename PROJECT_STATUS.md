# Chinese Graded Reader - Project Status
**Last Updated:** February 20, 2026

## Current State

All 20 stories are integrated into the app. The UI uses the **Jade Split** theme — a persistent two-pane sidebar layout with a dark teal sidebar and light mint reading pane.

**Live site:** https://helenct.github.io/claude-code-play/

### Navigation Model
- Dark teal sidebar: logo, HSK level nav (vertical stack), scrollable story list
- Light mint main pane: story title, genre badge, instruction text, word-segmented content
- Selecting a level populates the story list and auto-selects the first story
- Selecting a story renders it in the reading pane

### Known Issue
- 会说话的书 (HSK 1, Sci-Fi) is incomplete (~120 word entries vs ~200+ for other stories). The full version was never finished during story creation.

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
├── hsk_vocab.js            (HSK 1-4 vocab sets, above-level detection)
├── data/
│   └── texts.json          (all 20 stories, canonical data source)
├── PROJECT_STATUS.md
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
