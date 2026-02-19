# claude-code-play

Sandbox for playing with Claude Code

## Chinese Graded Reader Web App

A web-based Chinese language learning application with graded readers to help users practice reading at appropriate difficulty levels. Users can hover over unfamiliar words to see pronunciation (pinyin) and English translations.

## Features

- 4 difficulty levels (HSK 1-4)
- Each level contains ~500 characters of authentic Chinese text
- Interactive word tooltips showing pinyin and English translations
- Clean, modern interface with smooth transitions
- Responsive design for desktop and mobile devices
- No framework dependencies - pure vanilla JavaScript

## File Structure

```
/home/ubuntu/claude-code-play/
├── index.html              # Main HTML structure
├── styles.css              # All styling including tooltips
├── app.js                  # Application logic and state management
├── data/
│   └── texts.json         # Text content with word segmentation
└── README.md              # This file
```

## How to Run

Simply open `index.html` in a web browser. No server or build process required.

```bash
# If you want to use a local server (optional)
python -m http.server 8000
# Then open http://localhost:8000 in your browser
```

## Data Structure

The `data/texts.json` file contains all text content structured as follows:

```json
{
  "levels": [
    {
      "id": "hsk1",
      "name": "HSK 1",
      "title": "在咖啡馆",
      "description": "Beginner level - Basic daily conversations",
      "content": [
        {
          "text": "你好",
          "pinyin": "nǐ hǎo",
          "translation": "hello"
        },
        {
          "text": "！",
          "pinyin": null,
          "translation": null
        }
        // ... more words
      ]
    }
    // ... more levels
  ]
}
```

### Data Schema

- **levels**: Array of level objects
  - **id**: Unique identifier for the level
  - **name**: Display name (e.g., "HSK 1")
  - **title**: Title of the text in Chinese
  - **description**: Brief description of the level
  - **content**: Array of word objects
    - **text**: The Chinese word or punctuation
    - **pinyin**: Pronunciation (null for punctuation)
    - **translation**: English meaning (null for punctuation)

## Content Overview

### HSK 1 - 在咖啡馆 (At the Café)
Beginner level story about visiting a café with a friend. Uses basic vocabulary and simple sentence structures.

### HSK 2 - 周末计划 (Weekend Plans)
Elementary level story about making plans to watch a movie with a friend. Introduces time expressions and more complex sentences.

### HSK 3 - 第一次坐地铁 (First Time Taking the Subway)
Intermediate level story about taking the subway for the first time. Uses compound sentences and more advanced grammar patterns.

### HSK 4 - 中国茶文化 (Chinese Tea Culture)
Upper intermediate level essay about Chinese tea culture and traditions. Features complex sentence structures and cultural vocabulary.

## Technical Details

### Word Segmentation
The app uses word-based (词) segmentation instead of character-based segmentation. This is more natural for language learning since:
- Chinese words are the meaningful units
- HSK vocabulary is word-based
- Translations and pinyin make more sense at word level

### Tooltip Implementation
Tooltips are implemented using pure CSS with `::after` and `::before` pseudo-elements. This provides excellent performance without JavaScript overhead on hover events.

### Browser Compatibility
- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid and Flexbox for layouts
- UTF-8 encoding for proper Chinese character support

## Customization

### Adding New Texts
To add new texts or levels, edit `data/texts.json`:
1. Add a new level object to the `levels` array
2. Segment the text into words
3. Provide pinyin and translation for each word
4. Set `pinyin` and `translation` to `null` for punctuation

### Styling
All styles are in `styles.css`. You can customize:
- Colors (see the `header h1` and `.word:hover` rules)
- Font sizes (default is 24px for Chinese text)
- Tooltip appearance (`.word[data-pinyin]:hover::after`)
- Layout and spacing

## License

This project is created for educational purposes.

## Credits

Developed as a Chinese language learning tool to help students practice reading at appropriate difficulty levels.
