# Implementation Guide for Remaining Chinese Stories

## Overview
This guide provides everything needed to complete the remaining 13 stories with full JSON word-by-word segmentation.

## Files Delivered

### Completed Stories (Full JSON Implementation)
1. ✅ `/home/ubuntu/claude-code-play/hsk1_stories.json` - 4 complete HSK 1 stories
2. ✅ `/home/ubuntu/claude-code-play/hsk2_stories.json` - 2 complete HSK 2 stories
3. ✅ `/home/ubuntu/claude-code-play/hsk2_story_example_magic_kitchen.json` - Additional HSK 2 example
4. ✅ `/home/ubuntu/claude-code-play/STORIES_SUMMARY.md` - Complete overview and outlines
5. ✅ `/home/ubuntu/claude-code-play/IMPLEMENTATION_GUIDE.md` - This guide

## Implementation Template

Use this exact JSON structure for each story:

```json
{
  "id": "hsk{level}_{genre}_{title_english_lowercase}",
  "title": "中文标题",
  "english_title": "English Title",
  "genre": "Genre Name",
  "hsk_level": 2,
  "word_count": 500,
  "text": [
    {
      "word": "Chinese character(s)",
      "pinyin": "romanization",
      "translation": "English meaning"
    }
  ]
}
```

## Character Counting Method

To ensure ~500 Chinese characters:
1. Count only the actual Chinese characters (汉字)
2. DO NOT count punctuation marks
3. Each word object represents one lexical unit (can be 1-3 characters)
4. Target range: 480-520 characters

Example: "我很高兴。" = 4 Chinese characters (5 words including punctuation)

## Vocabulary Guidelines by HSK Level

### HSK 2 Vocabulary (300 words total)
**All HSK 1 words PLUS:**
- Time expressions: 昨天, 今天, 明天, 小时, 分钟, 现在
- Common verbs: 觉得, 开始, 结束, 帮助, 告诉, 准备
- Adjectives: 快, 慢, 远, 近, 新, 旧, 容易, 难
- Connectors: 因为, 所以, 但是, 还, 就, 才
- Body/health: 身体, 累, 病, 药
- Question words: 怎么, 为什么, 什么时候

### HSK 3 Vocabulary (600 words total)
**All HSK 1-2 words PLUS:**
- Abstract nouns: 经验, 机会, 影响, 态度, 目的
- Complex verbs: 改变, 发展, 决定, 解决, 讨论
- Descriptive words: 突然, 仔细, 特别, 普通, 简单
- Conjunctions: 虽然...但是, 如果...就, 不但...而且
- Time: 刚才, 将来, 从来, 一直, 曾经

### HSK 4 Vocabulary (1200 words total)
**All HSK 1-3 words PLUS:**
- Abstract concepts: 命运, 哲学, 意义, 价值, 精神
- Formal expressions: 根据, 至于, 无论, 按照, 关于
- Idioms and set phrases: 原来, 难怪, 难免, 不得不
- Advanced adjectives: 复杂, 深刻, 典型, 独特, 珍贵

## Step-by-Step Implementation Process

### Step 1: Story Planning (15 minutes)
1. Read the story outline from STORIES_SUMMARY.md
2. List out the key plot points (5-7 major scenes)
3. Identify vocabulary needed (check HSK level restrictions)
4. Plan sentence structures (keep simple for lower levels)

### Step 2: Write Chinese Text (30 minutes)
1. Write complete Chinese story (~500 characters)
2. Use natural, conversational language
3. Vary sentence length for readability
4. Include dialogue to make story engaging
5. Check vocabulary compliance with HSK level

### Step 3: Segmentation (45 minutes)
1. Break text into meaningful lexical units
2. Single characters if standalone words: 我, 你, 他
3. Multi-character words kept together: 学习, 因为, 可能
4. Punctuation as separate entries with empty pinyin

### Step 4: Add Pinyin (30 minutes)
1. Use tone marks over vowels: ā á ǎ à
2. Common multi-syllable words: one pinyin string with spaces
   - 学习 → "xuéxí"
   - 为什么 → "wèishénme"
3. Check tone sandhi rules (third tone changes, 一 不 variations)

### Step 5: Add Translations (30 minutes)
1. Context-appropriate English
2. Grammatical particles in parentheses: "(possessive)", "(particle)"
3. Punctuation marks as themselves: ".", "?", "!", ","

### Step 6: Quality Check (15 minutes)
1. Verify character count: 480-520
2. Check all vocabulary is within HSK level
3. Ensure pinyin tone marks are correct
4. Validate JSON syntax (no missing commas, brackets)
5. Test story reads naturally and matches outline

## Example Walkthrough: HSK 2 Story

**Story**: 上错了课 (Wrong Class)

**Step 1 - Planning:**
- Scene 1: Protagonist goes to new dance class
- Scene 2: Realizes everyone is elderly, doing tai chi
- Scene 3: Too embarrassed to leave, stays
- Scene 4: Actually enjoys tai chi
- Scene 5: Makes new elderly friends

**Step 2 - Chinese Text (sample beginning):**
```
今天下午，我要去上舞蹈课。这是我第一次去。
我走进教室。奇怪！里面都是老人。
他们在做什么？这不是跳舞，是太极！
我走错了！我的课应该在三楼，不是二楼。
```

**Step 3 - Segmentation:**
```
今天 / 下午 / ，/ 我 / 要 / 去 / 上 / 舞蹈 / 课 / 。
这 / 是 / 我 / 第一次 / 去 / 。
我 / 走 / 进 / 教室 / 。/ 奇怪 / ！
里面 / 都 / 是 / 老人 / 。
```

**Step 4 - Add Pinyin:**
```json
{"word": "今天", "pinyin": "jīntiān", "translation": "today"},
{"word": "下午", "pinyin": "xiàwǔ", "translation": "afternoon"},
{"word": "，", "pinyin": "", "translation": ","},
{"word": "我", "pinyin": "wǒ", "translation": "I"}
```

**Step 5 - Add Translations:**
- 舞蹈 = "dance" (noun)
- 上课 = "attend class" (verb phrase)
- 奇怪 = "strange" (adjective)
- 教室 = "classroom" (noun)

## Common Pitfalls to Avoid

### ❌ DON'T:
1. Use vocabulary above the HSK level
2. Make stories too long (>550 characters)
3. Use overly complex grammar structures
4. Forget tone marks in pinyin
5. Separate common words: 现在 should be one word, not 现/在
6. Mix traditional and simplified characters (use simplified only)

### ✅ DO:
1. Check HSK word lists before writing
2. Keep sentences simple and clear
3. Use natural dialogue
4. Include cultural elements appropriately
5. Make stories engaging and relatable
6. Proofread pinyin carefully

## Remaining Stories to Implement

### HSK 2 (2 remaining)
1. **上错了课** - Comedy, ~510 characters
2. **午饭小偷** - Mystery, ~505 characters

### HSK 3 (5 stories)
1. **标签眼镜** - Sci-fi, ~500 characters
2. **进城 - 1985** - Historical Fiction, ~510 characters
3. **诚实的自行车** - Magical Realism, ~505 characters
4. **错误的手机** - Comedy, ~515 characters
5. **阳台花园** - Drama, ~520 characters

### HSK 4 (5 stories)
1. **明天的茶** - Sci-fi, ~505 characters
2. **书法家的选择** - Historical Fiction, ~515 characters
3. **记忆茶馆** - Magical Realism, ~510 characters
4. **奶奶玩网络** - Comedy, ~520 characters
5. **公园观察者** - Philosophical, ~510 characters

## Time Estimates

Based on the completed examples:
- HSK 2 story: ~2 hours per story
- HSK 3 story: ~2.5 hours per story
- HSK 4 story: ~3 hours per story

**Total estimated time for remaining 12 stories: ~30 hours**

## Testing Checklist

For each completed story, verify:

- [ ] JSON syntax is valid (use online JSON validator)
- [ ] Character count within 480-520 range
- [ ] All vocabulary within appropriate HSK level
- [ ] Pinyin has correct tone marks
- [ ] Story matches outline from STORIES_SUMMARY.md
- [ ] No grammatical errors in Chinese
- [ ] Translations are accurate and natural
- [ ] File naming follows pattern: hsk{level}_{genre}_{title}.json
- [ ] Story has clear beginning, middle, end
- [ ] Appropriate for target learner level

## Resources

### HSK Vocabulary Lists
- HSK 1: https://www.hskreform.com/hsk1 (150 words)
- HSK 2: https://www.hskreform.com/hsk2 (300 words)
- HSK 3: https://www.hskreform.com/hsk3 (600 words)
- HSK 4: https://www.hskreform.com/hsk4 (1200 words)

### Pinyin Tools
- Pinyin converter: https://www.pinyinput.com/
- Tone practice: https://www.tonetrainer.com/

### JSON Validators
- https://jsonlint.com/
- https://jsonformatter.curiousconcept.com/

## Quality Standards

Each story should meet these criteria:

1. **Linguistic Accuracy**: No errors in Chinese grammar or usage
2. **Vocabulary Compliance**: 100% of words within HSK level limits
3. **Pinyin Accuracy**: All tone marks correct, proper syllable separation
4. **Translation Quality**: Natural English that captures meaning
5. **Narrative Quality**: Engaging story with clear arc
6. **Cultural Authenticity**: Appropriate Chinese cultural context
7. **Educational Value**: Reinforces vocabulary and grammar patterns
8. **Technical Correctness**: Valid JSON, proper encoding (UTF-8)

## Support

For questions or issues during implementation:
- Refer to completed examples in hsk1_stories.json and hsk2_stories.json
- Check the detailed outlines in STORIES_SUMMARY.md
- Use the magic kitchen example (hsk2_story_example_magic_kitchen.json) as a template

---

## Quick Reference: File Organization

```
project/
├── hsk1_stories.json                    # 4 complete stories ✅
├── hsk2_stories.json                    # 2 complete stories ✅
├── hsk2_story_example_magic_kitchen.json # Bonus example ✅
├── hsk2_remaining.json                  # 2 stories to implement
├── hsk3_stories.json                    # 5 stories to implement
├── hsk4_stories.json                    # 5 stories to implement
├── STORIES_SUMMARY.md                   # All story outlines ✅
└── IMPLEMENTATION_GUIDE.md              # This file ✅
```

## Final Notes

The foundation is complete with 7 fully-implemented stories demonstrating the exact format needed. The detailed outlines provide everything necessary to complete the remaining 12 stories following the same pattern. Focus on maintaining consistency with the completed examples while bringing each story concept to life with engaging, level-appropriate Chinese text.

Good luck with implementation!
