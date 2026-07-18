// COLLECTION ITEM PICKER SEARCH — live-filters the grouped checkbox list on the collection
// upload/edit pages. Filtering only hides rows visually; checked state is untouched, so items
// checked while filtered still submit.
document.addEventListener('input', (event) => {

    const input = event.target.closest('.upload-picker-search');
    if (!input) return;

    const group = input.closest('.auth-field-group');
    const picker = group.querySelector('.upload-item-picker');
    const query = input.value.trim().toLowerCase();

    picker.querySelectorAll('.upload-item-picker-row').forEach((row) => {
        row.hidden = query !== '' && !row.textContent.toLowerCase().includes(query);
    });

    // A category heading with every row under it hidden should disappear too.
    picker.querySelectorAll('.upload-item-picker-group').forEach((heading) => {
        let node = heading.nextElementSibling;
        let anyVisible = false;
        while (node && !node.classList.contains('upload-item-picker-group')) {
            if (node.classList.contains('upload-item-picker-row') && !node.hidden) anyVisible = true;
            node = node.nextElementSibling;
        }
        heading.hidden = !anyVisible;
    });

    const noResults = picker.querySelector('.upload-picker-no-results');
    if (noResults) noResults.hidden = picker.querySelector('.upload-item-picker-row:not([hidden])') !== null;
});

// SELECTED COUNT — the "N selected" badge next to the search bar. Initial value is rendered
// server-side, so this only has to react to checkbox changes.
document.addEventListener('change', (event) => {

    if (!event.target.matches('.upload-item-picker input[type="checkbox"]')) return;

    const group = event.target.closest('.auth-field-group');
    const badge = group.querySelector('.upload-picker-count');
    if (!badge) return;

    const count = group.querySelectorAll('.upload-item-picker input[type="checkbox"]:checked').length;
    badge.textContent = count + ' selected';
});

// The search box lives inside the main <form> — Enter must filter, never submit the collection.
document.addEventListener('keydown', (event) => {

    if (event.key === 'Enter' && event.target.closest('.upload-picker-search')) {
        event.preventDefault();
    }
});
