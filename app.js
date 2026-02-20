// Application state
let appData = null;
let currentLevel = null;
let currentStory = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    showLevelSelection();
});

// Load data from JSON file
async function loadData() {
    try {
        const response = await fetch('data/texts.json');
        if (!response.ok) {
            throw new Error('Failed to load data');
        }
        appData = await response.json();
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('app').innerHTML = `
            <div style="background: white; padding: 2rem; border-radius: 12px; text-align: center;">
                <h2 style="color: #e74c3c;">Error Loading Data</h2>
                <p>Failed to load the texts. Please make sure the data file exists.</p>
            </div>
        `;
    }
}

// Get HSK level number from level ID (e.g., "hsk2" -> 2)
function getLevelNumber(levelId) {
    return parseInt(levelId.replace('hsk', ''), 10);
}

// Render an array of word segments as hoverable spans
// hskLevel: optional number (1-4) to flag above-level words
function renderWords(segments, hskLevel) {
    return segments.map(item => {
        if (item.pinyin && item.translation) {
            const aboveClass = hskLevel && isAboveLevel(item.text, hskLevel) ? ' above-level' : '';
            return `<span class="word${aboveClass}" data-pinyin="${item.pinyin}" data-translation="${item.translation}">${item.text}</span>`;
        }
        return item.text;
    }).join('');
}

// Render a genre badge with Chinese text and hover tooltip
function renderGenreBadge(genre) {
    const data = GENRE_DATA[genre];
    if (data) {
        return `<span class="genre-badge word" data-pinyin="${data.pinyin}" data-translation="${data.english}">${data.chinese}</span>`;
    }
    return `<span class="genre-badge">${genre}</span>`;
}

// Show level selection view
function showLevelSelection() {
    currentLevel = null;
    currentStory = null;
    const appContainer = document.getElementById('app');

    if (!appData || !appData.levels) {
        appContainer.innerHTML = `
            <div style="background: white; padding: 2rem; border-radius: 12px; text-align: center;">
                <h2 style="color: #e74c3c;">Error</h2>
                <p>Unable to load content. Please refresh the page.</p>
            </div>
        `;
        return;
    }

    const levelCards = appData.levels.map(level => `
        <div class="level-card" onclick="navigateToLevel('${level.id}')">
            <h2>${level.name}</h2>
            <p class="description">${level.description}</p>
            <p class="story-count">${level.stories.length} stories</p>
        </div>
    `).join('');

    appContainer.innerHTML = `
        <div class="level-selection">
            ${levelCards}
        </div>
    `;
}

// Navigate to a specific level's story list
function navigateToLevel(levelId) {
    const level = appData.levels.find(l => l.id === levelId);
    if (level) {
        currentLevel = level;
        showStorySelection(level);
    }
}

// Show story selection view for a level
function showStorySelection(level) {
    currentStory = null;
    const appContainer = document.getElementById('app');
    const hskLevel = getLevelNumber(level.id);

    const storyCards = level.stories.map(story => `
        <div class="story-card" onclick="navigateToStory('${story.id}')">
            ${renderGenreBadge(story.genre)}
            <h3>${renderWords(story.title_segments, hskLevel)}</h3>
        </div>
    `).join('');

    appContainer.innerHTML = `
        <div class="story-selection">
            <div class="section-header">
                <h2>${level.name}</h2>
                <p class="description">${level.description}</p>
            </div>
            <div class="story-grid">
                ${storyCards}
            </div>
            <button class="back-button" onclick="showLevelSelection()">Back to Levels</button>
        </div>
    `;
}

// Navigate to a specific story
function navigateToStory(storyId) {
    const story = currentLevel.stories.find(s => s.id === storyId);
    if (story) {
        currentStory = story;
        showText(story);
    }
}

// Show text reading view
function showText(story) {
    const appContainer = document.getElementById('app');
    const hskLevel = getLevelNumber(currentLevel.id);

    const textContent = renderWords(story.content, hskLevel);

    appContainer.innerHTML = `
        <div class="reading-view">
            <div class="reading-header">
                <h2>${renderWords(story.title_segments, hskLevel)}</h2>
                ${renderGenreBadge(story.genre)}
                <p class="instruction">Hover over words to see pinyin and translation. <span class="above-level-hint">Dotted underline</span> = above level.</p>
            </div>
            <div class="text-content">
                ${textContent}
            </div>
            <button class="back-button" onclick="showStorySelection(currentLevel)">Back to Stories</button>
        </div>
    `;
}
