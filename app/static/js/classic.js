document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const crawlBtn = document.getElementById('crawl-btn');
    const readBtn = document.getElementById('read-btn');
    const paperList = document.getElementById('paper-list');
    const pdfViewer = document.getElementById('pdf-viewer');
    const summaryViewer = document.getElementById('summary-viewer');

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
        const selectedPapers = Array.from(document.querySelectorAll('.paper-item.selected'))
            .map(el => ({
                id: el.dataset.id,
                title: el.dataset.title,
                authors: JSON.parse(el.dataset.authors),
                abstract: el.dataset.abstract,
                pdf_url: el.dataset.pdfUrl,
                md_path: el.dataset.mdPath
            }));

        if (selectedPapers.length === 0) {
            alert('Please select at least one paper');
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

    // Display papers in list
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
                <h3>${paper.title}</h3>
                <p class="authors">${paper.authors.join(', ')}</p>
                <p class="abstract">${paper.abstract.substring(0, 100)}...</p>
            `;

            paperEl.addEventListener('click', () => {
                document.querySelectorAll('.paper-item').forEach(el => el.classList.remove('selected'));
                paperEl.classList.add('selected');
                showPaper(paper.id);
            });

            paperList.appendChild(paperEl);
        });
    }

    // Show paper in viewer
    async function showPaper(paperId) {
        // Show PDF
        pdfViewer.innerHTML = `
            <iframe src="/papers/semantic/${paperId}/pdf" 
                    width="100%" 
                    height="100%" 
                    style="border: none;"></iframe>
        `;

        // Show summary
        try {
            const response = await fetch(`/papers/semantic/${paperId}/summary`);
            if (response.ok) {
                const markdown = await response.text();
                // Initialize marked if not already loaded
                if (typeof marked === 'undefined') {
                    const script = document.createElement('script');
                    script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
                    script.onload = () => {
                        summaryViewer.innerHTML = marked.parse(markdown);
                    };
                    document.head.appendChild(script);
                } else {
                    summaryViewer.innerHTML = marked.parse(markdown);
                }
            } else {
                summaryViewer.innerHTML = '<p>No summary available yet. Click "Read Papers" to generate one.</p>';
            }
        } catch (error) {
            summaryViewer.innerHTML = '<p>Error loading summary</p>';
            console.error('Summary load failed:', error);
        }

        // Auto-refresh paper list every 30 seconds
        if (!window.paperRefreshInterval) {
            window.paperRefreshInterval = setInterval(() => {
                if (searchInput.value.trim()) {
                    searchBtn.click();
                }
            }, 30000);
        }
    }
});
