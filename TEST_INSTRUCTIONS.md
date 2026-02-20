# Testing Instructions

## Quick Start Test

1. Open `index.html` in a web browser:
   ```bash
   # Option 1: Direct file opening (may not work due to CORS)
   open index.html

   # Option 2: Use a local server (recommended)
   python3 -m http.server 8000
   # Then open http://localhost:8000 in your browser
   ```

2. **Expected Results:**

### Level Selection Screen
- You should see 4 cards displayed in a grid
- Each card shows:
  - HSK level (HSK 1, HSK 2, HSK 3, HSK 4)
  - Chinese title (在咖啡馆, 周末计划, etc.)
  - English description
- Cards should have a purple theme with hover effects (lift up on hover)

### Reading View
- Click any level card
- You should see:
  - The Chinese title at the top
  - Instruction text: "Hover over words to see pinyin and translation"
  - Chinese text with words having dotted underlines
  - A "Back to Levels" button at the bottom

### Tooltip Interaction
- Hover over any word with a dotted underline
- A dark tooltip should appear above the word showing:
  - Pinyin pronunciation
  - English translation
  - Format: "pinyin - translation"
- Example: Hovering over "你好" shows "nǐ hǎo - hello"

### Navigation
- Click "Back to Levels" button
- Should return to the level selection screen
- Try clicking different levels to verify all texts load correctly

## Automated Tests

Run these commands to verify the app structure:

```bash
# Validate JSON
python3 -m json.tool data/texts.json > /dev/null && echo "✓ JSON valid"

# Check file structure
ls -l index.html styles.css app.js data/texts.json && echo "✓ All files present"

# Count content
python3 << 'EOF'
import json
with open('data/texts.json', 'r') as f:
    data = json.load(f)
    for level in data['levels']:
        words = sum(1 for item in level['content'] if item['pinyin'])
        print(f"✓ {level['name']}: {words} hoverable words")
EOF
```

## Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## Mobile Testing

Test responsive design:
- [ ] Mobile portrait view (< 480px)
- [ ] Tablet view (768px)
- [ ] Desktop view (> 1200px)

## Known Limitations

1. **Mobile tooltips**: Currently uses CSS :hover, which works on tap for mobile but may not be ideal
2. **Tooltip positioning**: May clip at viewport edges for words at the edge of the screen
3. **Character count**: Texts are shorter than 500 chars (127-311) but have good word density

## Bug Fixes Applied

1. ✓ Added null check in `showLevelSelection()` to prevent crashes if data fails to load
2. ✓ Added error handling in `loadData()` with user-friendly error messages
3. ✓ Verified all data attributes are properly formatted without injection vulnerabilities
