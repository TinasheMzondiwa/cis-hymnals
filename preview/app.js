document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const fileNameDisplay = document.getElementById('fileName');
    const searchInput = document.getElementById('searchInput');
    const hymnListContainer = document.getElementById('hymnList');
    const contentArea = document.getElementById('contentArea');
    const clearSearchBtn = document.getElementById('clearSearch');

    let allHymns = [];
    let activeHymnNumber = null;

    // File Loading
    fileInput.addEventListener('click', () => {
        fileInput.value = ''; // Allow re-selecting the same file
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        fileNameDisplay.textContent = file.name;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                if (Array.isArray(data)) {
                    // Validation: Check for V2 format (must have 'lyrics' array)
                    const sample = data.find(h => h.number); // Find first valid item

                    if (!sample) {
                        alert("Invalid File ⚠️\n\nThis file does not appear to contain hymn data (no hymn numbers found).");
                        return;
                    }

                    if (sample) {
                        if (!sample.lyrics && sample.content) {
                            const v2Name = file.name.replace('.json', '_v2.json');
                            alert(`Legacy File Detected ⚠️\n\nYou opened a V1 file ('${file.name}').\nPlease select the V2 version ('${v2Name}') which contains the structured lyrics.`);
                            return;
                        }
                        if (!sample.lyrics) {
                            alert("Invalid Format ⚠️\n\nThis file does not appear to contain valid lyrics data.");
                            return;
                        }
                    }

                    allHymns = data;
                    renderHymnList(allHymns);
                    searchInput.disabled = false;

                    // Smart Refresh: Check if we had an active hymn and try to restore it
                    if (activeHymnNumber !== null) {
                        const savedHymn = allHymns.find(h => h.number === activeHymnNumber);
                        if (savedHymn) {
                            renderHymn(savedHymn);
                            // Also scroll hymn list to active item? (Optional refinement)
                        } else {
                            // Active hymn no longer exists (deleted/renumbered)
                            showEmptyState();
                        }
                    } else {
                        showEmptyState();
                    }
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

    function showEmptyState() {
        contentArea.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full text-gray-400 max-w-md text-center animate-pulse">
                <p class="text-sm font-medium">← Select a hymn from the list</p>
            </div>
        `;
    }

    // Search Filtering
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();

        // Toggle Clear Button
        if (term.length > 0) {
            clearSearchBtn.classList.remove('hidden');
        } else {
            clearSearchBtn.classList.add('hidden');
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
        clearSearchBtn.classList.add('hidden');
        renderHymnList(allHymns);
        searchInput.focus();
    });

    // Rendering List
    function renderHymnList(hymns) {
        hymnListContainer.innerHTML = '';

        if (hymns.length === 0) {
            hymnListContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center p-8 text-gray-400">
                    <p class="text-xs uppercase tracking-wide font-semibold">No hymns found</p>
                </div>
            `;
            return;
        }

        hymns.forEach(hymn => {
            const el = document.createElement('div');
            // Base styles
            el.className = 'group p-3 px-4 hover:bg-gray-50 cursor-pointer flex gap-3 text-sm transition-all border-l-4 border-transparent items-baseline';

            el.innerHTML = `
                <span class="font-bold text-gray-400 group-hover:text-gray-600 transition-colors min-w-[2.5ch] text-right tabular-nums">${hymn.number}</span>
                <span class="font-medium text-gray-700 group-hover:text-gray-900 truncate">${hymn.title}</span>
            `;

            el.addEventListener('click', () => {
                // Highlight active
                const activeClasses = ['bg-blue-50/50', 'border-primary', 'shadow-[inset_2px_0_0_0_var(--tw-shadow-color)]'];

                // Reset all
                document.querySelectorAll('#hymnList > div').forEach(item => {
                    item.classList.remove(...activeClasses);
                    item.classList.add('border-transparent');
                    item.querySelector('span:first-child').classList.remove('text-primary');
                    item.querySelector('span:first-child').classList.add('text-gray-400');
                });

                // Set active
                el.classList.remove('border-transparent');
                el.classList.add(...activeClasses);
                el.querySelector('span:first-child').classList.remove('text-gray-400');
                el.querySelector('span:first-child').classList.add('text-primary');

                renderHymn(hymn);
            });
            hymnListContainer.appendChild(el);
        });
    }

    // Render Single Hymn
    function renderHymn(hymn) {
        activeHymnNumber = hymn.number; // Save state for smart refresh

        // Main Card
        let html = `
            <div class="bg-white w-full max-w-2xl px-8 py-10 md:px-12 md:py-14 shadow-lg shadow-gray-200/50 rounded-xl mb-10 transition-all font-serif flex flex-col items-stretch">
                <!-- Header -->
                <div class="text-center mb-10 pb-6 border-b border-gray-100">
                    <h1 class="font-bold text-3xl text-gray-900 mb-2 leading-tight">${hymn.number}. ${hymn.title}</h1>
                    ${hymn.title_english ? `<div class="text-xs font-sans font-bold text-gray-400 uppercase tracking-widest mt-2">${hymn.title_english}</div>` : ''}
                </div>
                
                <!-- Body -->
                <div class="text-lg leading-relaxed text-gray-800 space-y-8">
        `;

        if (hymn.lyrics && Array.isArray(hymn.lyrics)) {
            hymn.lyrics.forEach(block => {
                const isRefrain = block.type === 'refrain';
                const labelText = isRefrain ? 'CHORUS' : `VERSE ${block.index}`;

                // Refrain Styling vs Verse Styling
                const containerClasses = isRefrain
                    ? 'relative pl-6 py-1 italic text-gray-600 border-l-4 border-primary/20 bg-gray-50/50 rounded-r-lg'
                    : 'relative';

                const labelClasses = isRefrain
                    ? 'absolute -top-3 left-6 bg-white px-1 text-[10px] font-sans font-bold text-primary uppercase tracking-widest'
                    : 'mb-1 text-[10px] font-sans font-bold text-gray-300 uppercase tracking-widest';

                html += `<div class="${containerClasses}">`;

                // Label
                html += `<div class="${labelClasses}">${labelText}</div>`;

                if (block.lines) {
                    block.lines.forEach(line => {
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
