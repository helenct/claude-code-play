// Application state
let appData = null;
let currentLevel = null;

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
    const appContainer = document.getElementById('app');

    // Check if data is loaded
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
            <div class="text-title">${level.title}</div>
            <p class="description">${level.description}</p>
        </div>
    `).join('');

    appContainer.innerHTML = `
        <div class="level-selection">
            ${levelCards}
        </div>
    `;
}

// Navigate to a specific level
function navigateToLevel(levelId) {
    const level = appData.levels.find(l => l.id === levelId);
    if (level) {
        currentLevel = level;
        showText(level);
    }
}

// Navigate back to level selection
function navigateBack() {
    showLevelSelection();
}

// Show text reading view
function showText(level) {
    const appContainer = document.getElementById('app');

    // Generate text with hoverable words
    const textContent = level.content.map(item => {
        if (item.pinyin && item.translation) {
            // Hoverable word
            return `<span class="word" data-pinyin="${item.pinyin}" data-translation="${item.translation}">${item.text}</span>`;
        } else {
            // Punctuation or non-hoverable text
            return item.text;
        }
    }).join('');

    appContainer.innerHTML = `
        <div class="reading-view">
            <div class="reading-header">
                <h2>${level.title}</h2>
                <p class="instruction">Hover over words to see pinyin and translation</p>
            </div>
            <div class="text-content">
                ${textContent}
            </div>
            <button class="back-button" onclick="navigateBack()">Back to Levels</button>
        </div>
    `;
}
