// READING LIST TOGGLE — bookmark button on detail pages
//
// One delegated listener handles every .reading-list-form on the page, intercepting the submit
// so toggling a reading-list entry is a background fetch instead of a full page navigation/reload.

document.addEventListener('submit', (e) => {

    const form = e.target.closest('.reading-list-form');

    if (!form) return;

    e.preventDefault();

    const button = form.querySelector('.reading-list-btn');
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

            button.classList.toggle('is-active', data.is_in_reading_list);
            button.setAttribute('aria-pressed', data.is_in_reading_list ? 'true' : 'false');
            button.setAttribute('aria-label', data.is_in_reading_list ? 'Remove from reading list' : 'Add to reading list');

            const svg = button.querySelector('svg');
            svg.setAttribute('fill', data.is_in_reading_list ? 'currentColor' : 'none');
        });
});
