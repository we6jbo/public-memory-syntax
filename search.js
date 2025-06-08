document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query');
    if (query) {
        searchMemory(query.toLowerCase());
    }
});

async function searchMemory(query) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    let found = false;

    // 1. GitHub search
    try {
        const githubResponse = await fetch(`https://api.github.com/repos/we6jbo/public-memory-syntax/contents`);
        const files = await githubResponse.json();
        for (const file of files) {
            if (file.name.toLowerCase().includes(query)) {
                const link = document.createElement('a');
                link.href = file.html_url;
                link.textContent = `GitHub: ${file.name}`;
                link.target = '_blank';
                resultsDiv.appendChild(link);
                resultsDiv.appendChild(document.createElement('br'));
                found = true;
            }
        }
    } catch (e) {
        console.error("GitHub search failed", e);
    }

    // 2. Twitter search
    const xHashtag = encodeURIComponent(`from:neal_jerem29652 #j03-project AND ${query}`);
    const xLink = document.createElement('a');
    xLink.href = `https://twitter.com/search?q=${xHashtag}`;
    xLink.textContent = `Search X (Twitter) for #j03-project ${query}`;
    xLink.target = '_blank';
    resultsDiv.appendChild(xLink);
    resultsDiv.appendChild(document.createElement('br'));

    // 3. Miraheze search (restricted to User:PublicMemorySyntax)
    const mirahezeLink = document.createElement('a');
    mirahezeLink.href = `https://meta.miraheze.org/w/index.php?search=User:PublicMemorySyntax/${encodeURIComponent(query)}&title=Special%3ASearch&profile=advanced&fulltext=1&ns2=1`;
    mirahezeLink.textContent = 'Search Personal Wiki at Miraheze';
    mirahezeLink.target = '_blank';
    resultsDiv.appendChild(mirahezeLink);
    resultsDiv.appendChild(document.createElement('br'));
    found = true;

    // 4. Fallback
    if (!found) {
        const fallbackLink = document.createElement('a');
        fallbackLink.href = 'https://j03.page/j03-project/';
        fallbackLink.textContent = 'Click here to view j03-project page';
        fallbackLink.target = '_blank';
        resultsDiv.appendChild(fallbackLink);
    }
}
