// HOME SPOTLIGHT SHUFFLE — "Discover Something New" row on the homepage
//
// The row is already randomized server-side on every page load (Content.objects.order_by('?')
// in core.views.home); this button re-rolls the same random set in place via fetch, without a
// full page reload, using core.views.shuffle_spotlight.

document.addEventListener('click', (e) => {

    const button = e.target.closest('#spotlight-shuffle-btn');

    if (!button) return;

    const grid = document.getElementById('spotlight-grid');

    if (!grid) return;

    button.disabled = true;

    fetch(button.dataset.shuffleUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
        .then((response) => response.json())
        .then((data) => {

            grid.innerHTML = '';

            data.items.forEach((item) => {
                const card = document.createElement('a');
                card.className = 'spotlight-item' + (item.cover_url ? ' has-cover' : '');
                card.href = item.url;

                if (item.cover_url) {
                    card.style.backgroundImage = `url('${item.cover_url}')`;
                }

                const title = document.createElement('span');
                title.textContent = item.title;
                card.appendChild(title);

                grid.appendChild(card);
            });
        })
        .finally(() => {
            button.disabled = false;
        });
});
