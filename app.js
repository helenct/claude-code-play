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

    const storyCards = level.stories.map(story => `
        <div class="story-card" onclick="navigateToStory('${story.id}')">
            <span class="genre-badge">${story.genre}</span>
            <h3><span class="word" data-pinyin="${story.title_pinyin}" data-translation="${story.title_english}">${story.title}</span></h3>
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

    const textContent = story.content.map(item => {
        if (item.pinyin && item.translation) {
            return `<span class="word" data-pinyin="${item.pinyin}" data-translation="${item.translation}">${item.text}</span>`;
        } else {
            return item.text;
        }
    }).join('');

    appContainer.innerHTML = `
        <div class="reading-view">
            <div class="reading-header">
                <h2>${story.title}</h2>
                <span class="genre-badge">${story.genre}</span>
                <p class="instruction">Hover over words to see pinyin and translation</p>
            </div>
            <div class="text-content">
                ${textContent}
            </div>
            <button class="back-button" onclick="showStorySelection(currentLevel)">Back to Stories</button>
        </div>
    `;
}
