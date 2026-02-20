// Application state
let appData = null;
let currentLevel = null;
let currentStory = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    initApp();
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
            <div style="padding: 2rem; text-align: center; grid-column: 1/-1;">
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
function renderWords(segments, hskLevel) {
    return segments.map(item => {
        if (item.pinyin && item.translation) {
            const aboveClass = hskLevel && isAboveLevel(item.text, hskLevel) ? ' above-level' : '';
            return `<span class="word${aboveClass}" data-pinyin="${item.pinyin}" data-translation="${item.translation}">${item.text}</span>`;
        }
        return item.text;
    }).join('');
}

// Render a genre badge with word-segmented Chinese text
function renderGenreBadge(genre) {
    const segments = GENRE_DATA[genre];
    if (segments) {
        return `<span class="genre-badge">${renderWords(segments)}</span>`;
    }
    return `<span class="genre-badge">${genre}</span>`;
}

// ── New sidebar/pane navigation model ──

function initApp() {
    if (!appData || !appData.levels) {
        document.getElementById('app').innerHTML = `
            <div style="padding: 2rem; text-align: center;">
                <h2 style="color: #e74c3c;">Error</h2>
                <p>Unable to load content. Please refresh the page.</p>
            </div>
        `;
        return;
    }

    const app = document.getElementById('app');
    app.innerHTML = `
        <nav class="sidebar">
            <div class="sidebar-logo">
                <h1>中文分级阅读</h1>
                <div class="subtitle">Chinese Graded Reader</div>
            </div>
            <div class="level-nav" id="level-nav"></div>
            <div class="story-list-section" id="story-list-section">
                <div class="story-list-heading">Stories</div>
                <div id="story-list"></div>
            </div>
        </nav>
        <div class="main-pane" id="main-pane">
            <div class="main-pane-empty">Select a story to begin reading</div>
        </div>
    `;

    renderLevelNav();
    // Auto-select first level
    selectLevel(appData.levels[0].id);
}

function renderLevelNav() {
    const container = document.getElementById('level-nav');
    container.innerHTML = appData.levels.map(level => {
        const count = level.stories.length;
        return `<button class="lv-item" data-level="${level.id}" onclick="selectLevel('${level.id}')">
            ${level.name}<span class="story-count">(${count})</span>
        </button>`;
    }).join('');
}

function selectLevel(levelId) {
    const level = appData.levels.find(l => l.id === levelId);
    if (!level) return;
    currentLevel = level;

    // Update active level highlight
    document.querySelectorAll('.lv-item').forEach(el => {
        el.classList.toggle('active', el.dataset.level === levelId);
    });

    renderStoryList(level);

    // Auto-select first story
    if (level.stories.length > 0) {
        selectStory(level.stories[0].id);
    }
}

function renderStoryList(level) {
    const container = document.getElementById('story-list');
    const hskLevel = getLevelNumber(level.id);

    container.innerHTML = level.stories.map(story => {
        const genreSegments = GENRE_DATA[story.genre];
        const genreText = genreSegments ? genreSegments.map(s => s.text).join('') : story.genre;
        return `<button class="story-item" data-story="${story.id}" onclick="selectStory('${story.id}')">
            ${story.title}<span class="story-genre">${genreText}</span>
        </button>`;
    }).join('');
}

function selectStory(storyId) {
    const story = currentLevel.stories.find(s => s.id === storyId);
    if (!story) return;
    currentStory = story;

    // Update active story highlight
    document.querySelectorAll('.story-item').forEach(el => {
        el.classList.toggle('active', el.dataset.story === storyId);
    });

    renderReading(story);
}

function renderReading(story) {
    const pane = document.getElementById('main-pane');
    const hskLevel = getLevelNumber(currentLevel.id);
    const textContent = renderWords(story.content, hskLevel);

    pane.innerHTML = `
        <h2 class="reading-title">${renderWords(story.title_segments, hskLevel)}</h2>
        <div class="reading-meta">
            ${renderGenreBadge(story.genre)}
            <span>${currentLevel.name}</span>
        </div>
        <hr class="reading-divider">
        <p class="reading-instruction">Hover over words to see pinyin and translation. <span class="above-level-hint">Dotted underline</span> = above your level.</p>
        <div class="text-content">
            ${textContent}
        </div>
    `;
}
