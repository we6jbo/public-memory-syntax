// background.js

// 1. On install, open the onboarding/help page
chrome.runtime.onInstalled.addListener(() => {
    chrome.tabs.create({ url: 'https://j03.page/2025/06/07/pin-extension/' });
});

// 2. Omnibox support
chrome.omnibox.onInputEntered.addListener((text) => {
    const searchUrl = `search.html?query=${encodeURIComponent(text)}`;
    chrome.tabs.create({ url: searchUrl });
});

// 3. Context menu support
chrome.contextMenus.create({
    id: "searchMemory",
    title: "Search Memory Locator for '%s'",
    contexts: ["selection"]
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "searchMemory" && info.selectionText) {
        const searchUrl = `search.html?query=${encodeURIComponent(info.selectionText)}`;
        chrome.tabs.create({ url: searchUrl });
    }
});
