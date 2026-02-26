// Application state
let appIndex = null;    // from data/index.json
let lexicon = null;     // from data/lexicon.json
let currentLevel = null;
let currentStoryId = null;
const storyCache = {};  // id → full story data

// Initialize the application
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    initApp();
});

// Load index and lexicon in parallel
async function loadData() {
    try {
        const [indexRes, lexiconRes] = await Promise.all([
            fetch('data/index.json'),
            fetch('data/lexicon.json'),
        ]);
        if (!indexRes.ok || !lexiconRes.ok) throw new Error('Failed to load data');
        appIndex = await indexRes.json();
        lexicon = await lexiconRes.json();
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('app').innerHTML = `
            <div style="padding: 2rem; text-align: center; grid-column: 1/-1;">
                <h2 style="color: #e74c3c;">Error Loading Data</h2>
                <p>Failed to load the application data. Please refresh the page.</p>
            </div>
        `;
    }
}

// Fetch a story file (with caching)
async function fetchStory(storyEntry) {
    if (storyCache[storyEntry.id]) return storyCache[storyEntry.id];
    const response = await fetch('data/' + storyEntry.file);
    if (!response.ok) throw new Error('Failed to load story: ' + storyEntry.id);
    const story = await response.json();
    storyCache[storyEntry.id] = story;
    return story;
}

// Check if a word is above the reader's current level
function isAboveLevel(word, readerLevel) {
    if (!lexicon || !readerLevel) return false;
    const entry = lexicon[word];
    if (!entry) return true;  // unknown word — flag it
    return entry.level > readerLevel;
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

// Render paragraphs (array of arrays of word segments)
function renderParagraphs(paragraphs, hskLevel) {
    return paragraphs.map(para =>
        `<p class="paragraph">${renderWords(para, hskLevel)}</p>`
    ).join('');
}

// Render a genre badge with word-segmented Chinese text
function renderGenreBadge(genre) {
    const segments = appIndex.genres[genre];
    if (segments) {
        return `<span class="genre-badge">${renderWords(segments)}</span>`;
    }
    return `<span class="genre-badge">${genre}</span>`;
}

// ── Sidebar/pane navigation ──

function initApp() {
    if (!appIndex || !appIndex.levels) {
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
    selectLevel(appIndex.levels[0].id);
}

function renderLevelNav() {
    const container = document.getElementById('level-nav');
    container.innerHTML = appIndex.levels.map(level => {
        const count = level.stories.length;
        return `<button class="lv-item" data-level="${level.id}" onclick="selectLevel('${level.id}')">
            ${level.name}<span class="story-count">(${count})</span>
        </button>`;
    }).join('');
}

function selectLevel(levelId) {
    const level = appIndex.levels.find(l => l.id === levelId);
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
    container.innerHTML = level.stories.map(story => {
        const genreSegments = appIndex.genres[story.genre];
        const genreText = genreSegments ? genreSegments.map(s => s.text).join('') : story.genre;
        return `<button class="story-item" data-story="${story.id}" onclick="selectStory('${story.id}')">
            ${story.title}<span class="story-genre">${genreText}</span>
        </button>`;
    }).join('');
}

async function selectStory(storyId) {
    const storyEntry = currentLevel.stories.find(s => s.id === storyId);
    if (!storyEntry) return;
    currentStoryId = storyId;

    // Update active story highlight
    document.querySelectorAll('.story-item').forEach(el => {
        el.classList.toggle('active', el.dataset.story === storyId);
    });

    try {
        const story = await fetchStory(storyEntry);
        // Guard: user may have clicked a different story while this one was loading
        if (currentStoryId !== storyId) return;
        renderReading(story);
    } catch (error) {
        console.error('Error loading story:', error);
        if (currentStoryId !== storyId) return;
        document.getElementById('main-pane').innerHTML = `
            <div class="main-pane-empty">Failed to load story. Please try again.</div>
        `;
    }
}

function renderReading(story) {
    const pane = document.getElementById('main-pane');
    const hskLevel = getLevelNumber(currentLevel.id);

    pane.innerHTML = `
        <h2 class="reading-title">${renderWords(story.title_segments, hskLevel)}</h2>
        <div class="reading-meta">
            ${renderGenreBadge(story.genre)}
            <span>${currentLevel.name}</span>
        </div>
        <hr class="reading-divider">
        <p class="reading-instruction">Hover over words to see pinyin and translation. <span class="above-level-hint">Dotted underline</span> = above your level.</p>
        <div class="text-content">
            ${renderParagraphs(story.content, hskLevel)}
        </div>
    `;
}
