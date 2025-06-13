document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const crawlBtn = document.getElementById('crawl-btn');
    const readBtn = document.getElementById('read-btn');
    const paperList = document.getElementById('paper-list');

    // Search papers
    searchBtn.addEventListener('click', async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        try {
            const response = await fetch('/api/semantic/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            const data = await response.json();
            displayPapers(data.results);
        } catch (error) {
            console.error('Search failed:', error);
        }
    });

    // Crawl papers
    crawlBtn.addEventListener('click', async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        try {
            const response = await fetch('/api/semantic/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });
            const data = await response.json();
            if (data.status === 'success') {
                alert('Papers crawled successfully!');
            }
        } catch (error) {
            console.error('Crawl failed:', error);
        }
    });

    // Read papers
    readBtn.addEventListener('click', async () => {
        const selectedPapers = Array.from(document.querySelectorAll('.paper-item'))
            .map(el => ({
                id: el.dataset.id,
                title: el.dataset.title,
                authors: JSON.parse(el.dataset.authors),
                abstract: el.dataset.abstract,
                pdf_url: el.dataset.pdfUrl,
                md_path: el.dataset.mdPath
            }));

        if (selectedPapers.length === 0) {
            alert('Please search for papers first');
            return;
        }

        try {
            const response = await fetch('/api/semantic/read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(selectedPapers)
            });
            const data = await response.json();
            if (data.status === 'success') {
                alert('Papers are being processed!');
            }
        } catch (error) {
            console.error('Read failed:', error);
        }
    });

    // Display papers in list with full details
    function displayPapers(papers) {
        paperList.innerHTML = '';
        papers.forEach(paper => {
            const paperEl = document.createElement('div');
            paperEl.className = 'paper-item';
            paperEl.dataset.id = paper.id;
            paperEl.dataset.title = paper.title;
            paperEl.dataset.authors = JSON.stringify(paper.authors);
            paperEl.dataset.abstract = paper.abstract;
            paperEl.dataset.pdfUrl = paper.pdf_url;
            paperEl.dataset.mdPath = paper.md_path;

            paperEl.innerHTML = `
                <div class="paper-header">
                    <div class="paper-thumbnail">
                        <div class="placeholder">📄</div>
                    </div>
                    <h3>${paper.title}</h3>
                    <div class="paper-meta">
                        <span class="authors">👥 ${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? ' et al.' : ''}</span>
                        <span class="citation">🏛️ ${paper.citation_count || 'Unknown venue'}</span>
                        <span class="venue">🏛️ ${paper.venue || 'Unknown venue'}</span>
                        <span class="year">📅 ${paper.publication_date ? new Date(paper.publication_date).getFullYear() : 'Unknown year'}</span>
                    </div>
                </div>
                <div class="paper-abstract">
                    <p>${paper.abstract ? paper.abstract.substring(0, 200) + (paper.abstract.length > 200 ? '...' : '') : 'No abstract available'}</p>
                </div>
                <div class="paper-actions">
                    <button class="read-paper" data-id="${paper.id}">
                        <span>📄 Read Paper</span>
                    </button>
                    <button class="read-summary" data-id="${paper.id}">
                        <span>📝 Read Summary</span>
                    </button>
                </div>
            `;

            // Add click handlers for buttons
            paperEl.querySelector('.read-paper').addEventListener('click', (e) => {
                e.stopPropagation();
                window.location.href = `/papers/semantic/${paper.id}/pdf`;
            });

            paperEl.querySelector('.read-summary').addEventListener('click', (e) => {
                e.stopPropagation();
                window.location.href = `/papers/semantic/${paper.id}/summary`;
            });

            paperList.appendChild(paperEl);
        });
    }
});
