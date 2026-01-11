document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileName');
    const searchInput = document.getElementById('searchInput');
    const hymnListContainer = document.getElementById('hymnList');
    const contentArea = document.getElementById('contentArea');

    let allHymns = [];

    // File Loading
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        fileNameDisplay.textContent = file.name;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                if (Array.isArray(data)) {
                    allHymns = data;
                    renderHymnList(allHymns);
                    searchInput.disabled = false;

                    // Clear main content
                    contentArea.innerHTML = '<div class="empty-state-large"><p>Select a hymn from the list to view</p></div>';
                } else {
                    alert('Invalid JSON format. Expected an array of hymns.');
                }
            } catch (error) {
                console.error('Error parsing JSON:', error);
                alert('Error parsing JSON file.');
            }
        };
        reader.readAsText(file);
    });

    // Search Filtering
    const clearSearchBtn = document.getElementById('clearSearch');

    // Search Filtering
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();

        // Toggle Clear Button
        if (term.length > 0) {
            clearSearchBtn.hidden = false;
        } else {
            clearSearchBtn.hidden = true;
        }

        const filtered = allHymns.filter(h =>
            h.number.toString().includes(term) ||
            (h.title && h.title.toLowerCase().includes(term)) ||
            (h.title_english && h.title_english.toLowerCase().includes(term))
        );
        renderHymnList(filtered);
    });

    // Clear Button Logic
    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearSearchBtn.hidden = true;
        renderHymnList(allHymns);
        searchInput.focus();
    });

    // Rendering List
    function renderHymnList(hymns) {
        hymnListContainer.innerHTML = '';

        if (hymns.length === 0) {
            hymnListContainer.innerHTML = '<div class="empty-state-small">No hymns found</div>';
            return;
        }

        hymns.forEach(hymn => {
            const el = document.createElement('div');
            el.className = 'hymn-item';
            el.innerHTML = `
                <span class="hymn-number">${hymn.number}</span>
                <span class="hymn-title">${hymn.title}</span>
            `;
            el.addEventListener('click', () => {
                // Highlight active
                document.querySelectorAll('.hymn-item').forEach(i => i.classList.remove('active'));
                el.classList.add('active');
                renderHymn(hymn);
            });
            hymnListContainer.appendChild(el);
        });
    }

    // Render Single Hymn
    function renderHymn(hymn) {
        let html = `
            <div class="hymn-display">
                <div class="hymn-header">
                    <h1>${hymn.number}. ${hymn.title}</h1>
                    ${hymn.title_english ? `<div class="english-title">${hymn.title_english}</div>` : ''}
                </div>
                <div class="hymn-body">
        `;

        if (hymn.lyrics && Array.isArray(hymn.lyrics)) {
            hymn.lyrics.forEach(block => {
                const isRefrain = block.type === 'refrain';
                const labelText = isRefrain ? 'CHORUS' : `VERSE ${block.index}`;

                html += `<div class="block ${isRefrain ? 'refrain' : 'verse'}">`;

                // Add the label
                html += `<div class="block-label">${labelText}</div>`;

                if (block.lines) {
                    block.lines.forEach((line, lineIdx) => {
                        // Optional: Add verse number inline to first line? 
                        // The user asked for "verse numbers", the label "VERSE X" covers it.
                        // But traditional hymnals might just put "1." at start.
                        // Let's stick to the label "VERSE X" above the block as requested ("label Chorus for refrain verses").
                        html += `<div>${line}</div>`;
                    });
                }
                html += `</div>`;
            });
        }

        html += `
                </div>
            </div>
        `;
        contentArea.innerHTML = html;
        contentArea.scrollTop = 0; // Scroll to top
    }
});
