#!/usr/bin/env python3
"""
Build lexicon.json from story data + SUBTLEX-CH frequency data + hanziDB character data.

Usage:
    python3 scripts/build-lexicon.py

Reads:
    data/texts.json                          — current story data (extracts all unique words)
    reference/SUBTLEX_CH_131210_CE.utf8      — word frequency, pinyin, POS, English translations
    reference/hanzi_db.csv                   — character frequency, pinyin, definitions

Writes:
    data/lexicon.json                        — canonical vocabulary file
"""

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORIES_FILE = ROOT / "data" / "texts.json"
SUBTLEX_FILE = ROOT / "reference" / "SUBTLEX_CH_131210_CE.utf8"
HANZIDB_FILE = ROOT / "reference" / "hanzi_db.csv"
OUTPUT_FILE = ROOT / "data" / "lexicon.json"

# Pinyin overrides for words where SUBTLEX's reading order is wrong
# or where we want a specific canonical reading for the reader app.
PINYIN_OVERRIDES = {
    "说": "shuō",
    "吗": "ma",
    "吧": "ba",
    "呢": "ne",
    "啊": "a",
    "嘛": "ma",
    "了": "le",
    "的": "de",
    "地": "de",
    "着": "zhe",
    "过": "guò",
    "给": "gěi",
    "要": "yào",
    "得": "de",
    "还": "hái",
    "都": "dōu",
    "会": "huì",
    "看": "kàn",
    "那": "nà",
    "哪": "nǎ",
    "和": "hé",
    "行": "xíng",
    "长": "cháng",
    "觉": "jué",
    "干": "gàn",
    "把": "bǎ",
    "当": "dāng",
    "不": "bù",
    "一": "yī",
    "个": "gè",
    "没": "méi",
    "来": "lái",
    "让": "ràng",
    "做": "zuò",
    "对": "duì",
    "走": "zǒu",
    "出": "chū",
    "回": "huí",
    "只": "zhǐ",
    "觉": "jué",
    "觉得": "juéde",
    "长": "cháng",
    "种": "zhǒng",
    "为": "wèi",
    "为了": "wèile",
    "地": "de",
    "了解": "liǎojiě",
    "当": "dāng",
    "发": "fā",
    "乐": "lè",
    "快乐": "kuàilè",
    "音乐": "yīnyuè",
    "重": "zhòng",
    "重要": "zhòngyào",
    "重新": "chóngxīn",
    "难": "nán",
    "中": "zhōng",
    "面": "miàn",
    "教": "jiāo",
    "好像": "hǎoxiàng",
    "什么样": "shénmeyàng",
    "这样": "zhèyàng",
    "时候": "shíhou",
    "东西": "dōngxi",
    "名字": "míngzi",
    "孩子": "háizi",
    "朋友": "péngyou",
    "先生": "xiānsheng",
    "学生": "xuésheng",
}

# Level bands: (min_rank, max_rank) -> level
# Words with freq_rank <= 150 are level 1, 151-400 level 2, etc.
LEVEL_BANDS = [
    (1, 150, 1),
    (151, 400, 2),
    (401, 800, 3),
    (801, 1500, 4),
    (1501, 3000, 5),
    (3001, 5000, 6),
]

# Pedagogical overrides: word -> forced level
# These override the frequency-based level assignment.
# Grammatically complex words bumped up despite high frequency:
PEDAGOGICAL_OVERRIDES = {
    "把": 3,       # #40 — disposal construction, grammatically complex
    "被": 3,       # #65 — passive marker, requires passive grammar
    "得": 2,       # #49 — complement marker, 3 readings (de/dé/děi)
    "如果": 2,     # #60 — conditional "if", requires conditional grammar
    "而": 3,       # #112 — literary conjunction, not beginner material
    "之": 4,       # literary possessive/nominalizer
    "于": 4,       # literary preposition
    "其": 4,       # literary pronoun "its/that"
    # Subtitle artifacts / interjections — not pedagogically urgent:
    "嘿": 3,       # #109 — "hey", subtitle artifact
    "嗯": 3,       # #128 — "um/uh-huh", filler
    "噢": 3,       # #149 — "oh", interjection
    "哦": 2,       # #63 — "oh", very common in speech though
    "啊": 2,       # #38 — modal particle, common but grammatically nuanced
    "嘛": 3,       # modal particle
    "呗": 4,       # modal particle, colloquial
    # Common words that should be level 1 despite borderline frequency:
    "说话": 1,     # #202 — "to speak", appears in HSK 1 story titles
    "爸爸": 1,     # family
    "妈妈": 1,     # family
    "老师": 1,     # teacher
    "学生": 1,     # student
    "学校": 1,     # school
    "朋友": 1,     # friend
    "今天": 1,     # today
    "明天": 1,     # tomorrow
    "昨天": 1,     # yesterday
    "喜欢": 1,     # to like
    "谢谢": 1,     # thank you
    "没有": 1,     # don't have
    "一个": 1,     # one (measure)
    "名字": 1,     # name
    "东西": 1,     # thing
    "时候": 1,     # time/when
    "孩子": 1,     # child
    "因为": 1,     # because
    "所以": 1,     # therefore
    "告诉": 1,     # to tell
    "开始": 1,     # to begin
    "已经": 1,     # already
    "但是": 1,     # but
    "可以": 1,     # can
    "什么": 1,     # what
    "怎么": 1,     # how
    "为什么": 1,   # why
    "现在": 1,     # now
    "问题": 1,     # question/problem
    "一起": 1,     # together
    "时间": 1,     # time
    "工作": 1,     # work
    "然后": 1,     # then
    "事情": 2,     # matter/affair
    "非常": 2,     # very much
    "希望": 2,     # to hope
    "当然": 2,     # of course
    "也许": 2,     # perhaps
    "相信": 2,     # to believe
    # Compounds of very basic words — should not be high-level:
    "不是": 1,     # #4941 as compound but 不(#6) + 是(#4) are both top 10
    "就是": 1,     # is exactly — 就(#13) + 是(#4)
    "还有": 1,     # also have — 还(#39) + 有(#11)
    "可能": 1,     # maybe — #100
    "看到": 2,     # saw — 看(#50) + 到(#35)
    "找到": 2,     # found — 找(#94) + 到(#35)
    "出来": 2,     # to come out — #198
    "回来": 2,     # to come back
    "起来": 2,     # to get up — #117
    "发现": 2,     # to discover — #170
    "每天": 2,     # every day — #768 but 每 + 天 are both basic
    "哪里": 2,     # where — #273
    "给": 1,       # to give/for — #43, extremely basic
    "问": 1,       # to ask — #201, basic verb
    "后来": 2,     # afterwards
    "自己": 2,     # oneself — #73
    "只": 2,       # only
    "又": 2,       # again
    "先": 2,       # first
    "最后": 2,     # finally
    "一些": 2,     # some
    "觉得": 1,     # to feel/think — #87
    "别人": 2,     # other people
    "地方": 2,     # place
    "发生": 2,     # to happen
    "准备": 2,     # to prepare
    "特别": 2,     # especially
    "一定": 2,     # certainly
    "声音": 2,     # sound/voice
    "以前": 2,     # before/previously
    "突然": 2,     # suddenly
    "终于": 3,     # finally
    "记得": 2,     # to remember
    # Core vocabulary that's lower-frequency in movie subtitles but
    # fundamental for a reading/learning context:
    "书": 1,       # #464 — book (core to a reading app!)
    "字": 1,       # #1138 — character/word
    "学习": 1,     # #1218 — to study
    "高兴": 1,     # #236 — happy
    "写": 1,       # #269 — to write
    "喝": 1,       # #264 — to drink
    "买": 1,       # #246 — to buy
    "住": 1,       # #209 — to live
    "认识": 1,     # #260 — to know (a person)
    "坐": 1,       # #261 — to sit
    "新": 1,       # #229 — new
    "狗": 2,       # #299 — dog
    "猫": 2,       # cat
    "家": 1,       # #157 — home/family
    "门": 2,       # #389 — door
    "本": 1,       # #338 — measure word for books
    "茶": 2,       # #2028 — tea (low in subtitles but basic vocab)
    "读": 2,       # #686 — to read
    "白": 2,       # #1106 — white (basic color)
    "五": 1,       # #563 — five (basic number)
    "下午": 1,     # #1026 — afternoon (basic time word)
    "晚上": 1,     # #368 — evening
    "早上": 2,     # #655 — morning
    "打开": 2,     # #652 — to open
    "漂亮": 2,     # #323 — beautiful/pretty
    "好像": 2,     # #316 — to seem like
    "里面": 2,     # #347 — inside
    "回家": 1,     # #373 — go home
    "看见": 1,     # #312 — to see
    "出去": 1,     # #310 — to go out
    "多少": 1,     # #360 — how many
    "同学": 2,     # #2388 — classmate
    "你好": 1,     # #2021 — hello (greeting, essential level 1)
    "邻居": 3,     # #1521 — neighbor
    "中文": 2,     # #9436 — very low frequency but essential for a Chinese reader app
    "读书": 2,     # #3400 — to study/read books
    "学校": 1,     # school
    "旁边": 2,     # #1356 — beside
    "块": 1,       # #372 — measure word for money
    "笑": 2,       # #504 — to laugh
    "高": 2,       # #454 — tall/high
    "外面": 2,     # #585 — outside
    "动": 2,       # #409 — to move
    "跳": 2,       # #404 — to jump
    "回答": 2,     # #769 — to answer
    "可爱": 2,     # #599 — cute
    "真的": 2,     # #622 — really
    "卖": 2,       # #448 — to sell
    "玩": 1,       # #282 — to play
    # Daily life vocabulary that's lower in subtitle frequency:
    "菜": 2,       # #1040 — dish/vegetable, basic food word
    "课": 2,       # #1089 — class/lesson, basic school word
    "鱼": 2,       # #1161 — fish, basic food word
    "星期": 2,     # #1075 — week, basic time word
    "手机": 2,     # #857 — mobile phone, very common
    "午饭": 3,     # #1946 — lunch, basic meal word
    "学": 2,       # #544 — to learn, fundamental
    "奶奶": 2,     # family word
    "爷爷": 2,     # family word
    "哥哥": 2,     # family word
    "姐姐": 2,     # family word
    "弟弟": 2,     # family word
    "妹妹": 2,     # family word
    "红": 2,       # red, basic color
    "黑": 2,       # black, basic color
    "蓝": 2,       # blue, basic color
    "黄": 3,       # yellow
    "绿": 3,       # green
    "地图": 3,     # #2196 — map
    "自行车": 3,   # #3798 — bicycle, common transport
    "眼镜": 3,     # #1918 — glasses
    "教室": 2,     # classroom
    "医院": 2,     # hospital
    "飞机": 2,     # airplane
    "电话": 2,     # telephone
    "电脑": 2,     # computer
    "生日": 2,     # birthday
    "天气": 2,     # weather
    "水果": 2,     # fruit
    "牛奶": 2,     # milk
    "信息": 3,     # information/message
}


def load_subtlex():
    """Load SUBTLEX-CH word frequency data."""
    words = {}
    rank = 0
    with open(SUBTLEX_FILE, "r", encoding="utf-8-sig") as f:
        header = f.readline()  # skip header
        for line in f:
            line = line.rstrip("\r\n")
            parts = line.split("\t")
            if len(parts) < 15:
                continue
            rank += 1
            word = parts[0]

            # Skip duplicate/corrupt entries (keep first occurrence = higher rank)
            if word in words:
                continue

            pinyin_raw = parts[2]       # e.g. "shui4/shuo1/yue4"
            pinyin_input = parts[3]     # e.g. "shuo" — indicates dominant reading
            pos = parts[10]             # dominant POS
            eng = parts[14]             # English translation

            # Select the dominant reading using pinyin_input as a guide
            pinyin_selected = select_dominant_pinyin(pinyin_raw, pinyin_input)

            words[word] = {
                "rank": rank,
                "pinyin_numbered": pinyin_selected,
                "pos": pos,
                "eng": eng,
            }
    return words


def select_dominant_pinyin(pinyin_raw, pinyin_input):
    """Select the dominant pronunciation from SUBTLEX alternatives.

    pinyin_raw: e.g. "shui4/shuo1/yue4" (all readings, numbered)
    pinyin_input: e.g. "shuo" (dominant reading, no tone number)

    Returns the numbered pinyin for the dominant reading.
    """
    if "/" not in pinyin_raw:
        return pinyin_raw  # single reading

    # For multi-character words, pinyin_raw has spaces: "bu4 shi5"
    # and pinyin_input is concatenated: "bushi"
    # In this case there are no alternatives, just return as-is
    if " " in pinyin_raw and "/" not in pinyin_raw:
        return pinyin_raw

    alternatives = pinyin_raw.split("/")

    # Match pinyin_input against alternatives (strip tone numbers for comparison)
    pinyin_input_clean = pinyin_input.lower().strip()
    for alt in alternatives:
        alt_stripped = "".join(c for c in alt if not c.isdigit()).lower().strip()
        if alt_stripped == pinyin_input_clean:
            return alt

    # If no exact match, try matching just the consonant+vowel skeleton
    for alt in alternatives:
        alt_base = "".join(c for c in alt if not c.isdigit()).lower().strip()
        if alt_base.startswith(pinyin_input_clean[:2]):
            return alt

    # Fallback: return first alternative
    return alternatives[0]


def load_hanzidb():
    """Load hanziDB character frequency data."""
    chars = {}
    with open(HANZIDB_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row["character"]
            try:
                freq_rank = int(row["frequency_rank"])
            except (ValueError, KeyError):
                continue
            chars[char] = {
                "rank": freq_rank,
                "pinyin": row.get("pinyin", ""),
                "definition": row.get("definition", ""),
            }
    return chars


def load_story_words():
    """Extract all unique words and their translations/pinyin from stories."""
    with open(STORIES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    words = {}  # word -> {"pinyin": set(), "translations": set()}
    for level in data["levels"]:
        for story in level["stories"]:
            # Content words
            for entry in story["content"]:
                text = entry.get("text", "")
                pinyin = entry.get("pinyin")
                translation = entry.get("translation")
                if not pinyin:  # skip punctuation
                    continue
                if text not in words:
                    words[text] = {"pinyin": set(), "translations": set()}
                words[text]["pinyin"].add(pinyin)
                if translation:
                    words[text]["translations"].add(translation)

            # Title segment words
            for entry in story.get("title_segments", []):
                text = entry.get("text", "")
                pinyin = entry.get("pinyin")
                translation = entry.get("translation")
                if not pinyin:
                    continue
                if text not in words:
                    words[text] = {"pinyin": set(), "translations": set()}
                words[text]["pinyin"].add(pinyin)
                if translation:
                    words[text]["translations"].add(translation)

    return words


def numbered_to_tone_mark(pinyin_numbered):
    """Convert numbered pinyin (e.g. 'wo3') to tone-marked (e.g. 'wǒ').

    Handles space-separated syllables and slash-separated alternatives.
    """
    tone_map = {
        "a": "āáǎàa",
        "e": "ēéěèe",
        "i": "īíǐìi",
        "o": "ōóǒòo",
        "u": "ūúǔùu",
        "ü": "ǖǘǚǜü",
        "v": "ǖǘǚǜü",  # v is sometimes used for ü
    }

    def convert_syllable(syl):
        syl = syl.strip()
        if not syl:
            return syl

        # Extract tone number (last char if digit)
        tone = 0
        if syl and syl[-1].isdigit():
            tone = int(syl[-1])
            syl = syl[:-1]

        if tone == 0 or tone == 5:
            # Neutral tone — no mark
            return syl.replace("v", "ü")

        # Find the vowel to place the tone mark on
        # Rules: (1) "a" or "e" gets it; (2) "ou" -> on "o"; (3) otherwise last vowel
        syl_lower = syl.lower()

        # Replace v with ü for lookup
        result = list(syl)
        for idx, ch in enumerate(result):
            if ch == "v":
                result[idx] = "ü"
            elif ch == "V":
                result[idx] = "Ü"

        vowels = "aeiouüÜ"
        vowel_indices = [i for i, c in enumerate(syl_lower) if c in "aeiouüv"]

        if not vowel_indices:
            return "".join(result)

        # Find which vowel gets the mark
        target = None
        for i in vowel_indices:
            if syl_lower[i] in ("a", "e"):
                target = i
                break
        if target is None:
            # "ou" -> mark on o
            for i in range(len(syl_lower) - 1):
                if syl_lower[i] == "o" and syl_lower[i + 1] == "u":
                    target = i
                    break
        if target is None:
            # Last vowel
            target = vowel_indices[-1]

        ch = result[target].lower()
        if ch in tone_map:
            marked = tone_map[ch][tone - 1]
            if result[target].isupper():
                marked = marked.upper()
            result[target] = marked

        return "".join(result)

    # Take only the first pronunciation if alternatives are given (separated by /)
    first_pinyin = pinyin_numbered.split("/")[0]

    # Handle space-separated syllables
    syllables = first_pinyin.split()
    converted = [convert_syllable(s) for s in syllables]
    return "".join(converted)


def estimate_level_from_chars(word, char_db):
    """Estimate word level from character frequencies when word isn't in SUBTLEX."""
    chinese_chars = [c for c in word if "\u4e00" <= c <= "\u9fff"]
    if not chinese_chars:
        return 4  # non-Chinese content, default to level 4

    max_char_rank = 0
    for c in chinese_chars:
        if c in char_db:
            max_char_rank = max(max_char_rank, char_db[c]["rank"])
        else:
            max_char_rank = 10000  # unknown character

    # Map max character rank to word level
    if max_char_rank <= 200:
        return 2
    elif max_char_rank <= 500:
        return 3
    elif max_char_rank <= 1000:
        return 4
    elif max_char_rank <= 2000:
        return 5
    else:
        return 6


def freq_rank_to_level(rank):
    """Convert a SUBTLEX frequency rank to a level using the band table."""
    for lo, hi, level in LEVEL_BANDS:
        if lo <= rank <= hi:
            return level
    # Beyond level 6 bands
    if rank > 5000:
        return 6
    return 6


def clean_subtlex_translation(eng):
    """Clean up SUBTLEX English translation for use in lexicon."""
    if not eng:
        return []

    # Remove surrounding quotes
    eng = eng.strip('"').strip()

    # SUBTLEX uses ; to separate meanings of different readings.
    # Take only the first reading's meanings (most common reading).
    first_reading = eng.split(";")[0].strip()

    meanings = []
    # Split on / for alternative meanings within same reading
    for sub in first_reading.split("/"):
        sub = sub.strip()
        if not sub:
            continue
        # Skip overly long definitions (parenthetical explanations)
        if len(sub) > 50:
            continue
        # Skip pure grammar notes in parens
        if sub.startswith("(") and sub.endswith(")"):
            continue
        # Skip cross-references like "see 游说[you2 shui4]"
        if sub.startswith("see "):
            continue
        # Skip entries that are mostly pinyin references like "variant of 哪[na3]"
        if "variant of" in sub:
            continue
        meanings.append(sub)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for m in meanings:
        m_lower = m.lower()
        if m_lower not in seen:
            seen.add(m_lower)
            unique.append(m)

    return unique[:5]  # cap at 5 meanings


def build_lexicon():
    print("Loading SUBTLEX-CH word frequency data...")
    subtlex = load_subtlex()
    print(f"  Loaded {len(subtlex)} words")

    print("Loading hanziDB character data...")
    char_db = load_hanzidb()
    print(f"  Loaded {len(char_db)} characters")

    print("Loading story words...")
    story_words = load_story_words()
    print(f"  Found {len(story_words)} unique words across all stories")

    lexicon = {}
    stats = {
        "in_subtlex": 0,
        "not_in_subtlex": 0,
        "overridden": 0,
        "levels": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
    }

    for word, story_data in sorted(story_words.items()):
        entry = {}

        if word in subtlex:
            sx = subtlex[word]
            stats["in_subtlex"] += 1

            # Pinyin: prefer SUBTLEX (numbered -> tone marks), fall back to story
            entry["pinyin"] = numbered_to_tone_mark(sx["pinyin_numbered"])
            entry["freq_rank"] = sx["rank"]
            entry["pos"] = sx["pos"] if sx["pos"] else None

            # Level: frequency-based, then check overrides
            entry["level"] = freq_rank_to_level(sx["rank"])

            # Meanings: merge SUBTLEX translations with story translations
            subtlex_meanings = clean_subtlex_translation(sx["eng"])
            story_meanings = sorted(story_data["translations"])
            # Story translations first (they're context-appropriate), then SUBTLEX
            all_meanings = []
            seen = set()
            for m in story_meanings + subtlex_meanings:
                m_lower = m.lower().strip()
                if m_lower and m_lower not in seen:
                    seen.add(m_lower)
                    all_meanings.append(m)
            entry["meanings"] = all_meanings[:8]

        else:
            stats["not_in_subtlex"] += 1

            # Use story pinyin (pick the most common one)
            pinyin_list = sorted(story_data["pinyin"])
            entry["pinyin"] = pinyin_list[0] if pinyin_list else ""
            entry["freq_rank"] = None
            entry["pos"] = None

            # Estimate level from character frequencies
            entry["level"] = estimate_level_from_chars(word, char_db)

            # Use story translations
            entry["meanings"] = sorted(story_data["translations"])

        # Apply pinyin overrides
        if word in PINYIN_OVERRIDES:
            entry["pinyin"] = PINYIN_OVERRIDES[word]

        # Apply pedagogical overrides
        if word in PEDAGOGICAL_OVERRIDES:
            old_level = entry["level"]
            entry["level"] = PEDAGOGICAL_OVERRIDES[word]
            if old_level != entry["level"]:
                stats["overridden"] += 1

        stats["levels"][entry["level"]] = stats["levels"].get(entry["level"], 0) + 1
        lexicon[word] = entry

    # Sort lexicon by level then frequency rank (None last) then word
    def sort_key(item):
        word, entry = item
        rank = entry["freq_rank"] if entry["freq_rank"] is not None else 999999
        return (entry["level"], rank, word)

    lexicon = dict(sorted(lexicon.items(), key=sort_key))

    # Write output
    print(f"\nWriting lexicon to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(lexicon, f, ensure_ascii=False, indent=2)

    # Print stats
    print(f"\n=== Lexicon Stats ===")
    print(f"Total words: {len(lexicon)}")
    print(f"In SUBTLEX-CH: {stats['in_subtlex']}")
    print(f"Not in SUBTLEX (estimated from chars): {stats['not_in_subtlex']}")
    print(f"Pedagogical overrides applied: {stats['overridden']}")
    print(f"\nWords per level:")
    for level in sorted(stats["levels"]):
        count = stats["levels"][level]
        print(f"  Level {level}: {count}")

    # Print words not in SUBTLEX for review
    not_in = [w for w, e in lexicon.items() if e["freq_rank"] is None]
    if not_in:
        print(f"\nWords not in SUBTLEX-CH ({len(not_in)}):")
        for w in not_in:
            e = lexicon[w]
            print(f"  {w} -> level {e['level']}, pinyin: {e['pinyin']}")

    return lexicon


if __name__ == "__main__":
    build_lexicon()
