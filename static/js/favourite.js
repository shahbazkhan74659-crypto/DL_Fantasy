// FAVOURITE TOGGLE — heart button on detail pages
//
// One delegated listener handles every .favourite-form on the page, intercepting the submit
// so toggling a favourite is a background fetch instead of a full page navigation/reload.

document.addEventListener('submit', (e) => {

    const form = e.target.closest('.favourite-form');

    if (!form) return;

    e.preventDefault();

    const button = form.querySelector('.favourite-btn');
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: new FormData(form),
    })
        .then((response) => response.json())
        .then((data) => {

            button.classList.toggle('is-active', data.is_favourited);
            button.setAttribute('aria-pressed', data.is_favourited ? 'true' : 'false');
            button.setAttribute('aria-label', data.is_favourited ? 'Remove from favourites' : 'Add to favourites');

            const svg = button.querySelector('svg');
            svg.setAttribute('fill', data.is_favourited ? 'currentColor' : 'none');
        });
});
