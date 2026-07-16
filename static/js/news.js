// NEWS MODAL — shared by "+ New" (create) and each card's "Edit" menu item

const newsOverlay = document.querySelector('#news-modal-overlay');
const newsModal = document.querySelector('#news-modal');
const newsForm = document.querySelector('#news-form');
const newsTitleInput = document.querySelector('#news-title');
const newsTagSelect = document.querySelector('#news-tag');
const newsBodyInput = document.querySelector('#news-body');
const newsCoverInput = document.querySelector('#news-cover-image');
const newsModalTitle = document.querySelector('#news-modal-title');
const newsSubmitBtn = document.querySelector('#news-submit-btn');
const newsCloseBtn = document.querySelector('#news-modal-close');
const newsCancelBtn = document.querySelector('#news-modal-cancel');
const newNewsBtn = document.querySelector('#new-news-btn');

function openNewsModal({ action, title, tag, body, heading, submitLabel }) {

    newsForm.action = action;
    newsTitleInput.value = title || '';
    newsTagSelect.value = tag || 'news';
    newsBodyInput.value = body || '';
    newsCoverInput.value = '';
    newsModalTitle.textContent = heading;
    newsSubmitBtn.textContent = submitLabel;

    openModal(newsOverlay, newsModal, newsTitleInput);
}

function closeNewsModal() {
    closeModal(newsOverlay, newsModal);
}

if (newsModal) {

    if (newNewsBtn) {

        newNewsBtn.addEventListener('click', () => openNewsModal({
            action: newNewsBtn.dataset.createUrl,
            heading: 'New Dispatch',
            submitLabel: 'Publish',
        }));
    }

    document.querySelectorAll('.news-edit-btn').forEach((btn) => {

        btn.addEventListener('click', () => {

            const menu = btn.closest('.card-menu');

            if (menu) {
                menu.classList.remove('is-open');
                const toggle = menu.querySelector('.card-menu-toggle');
                if (toggle) toggle.setAttribute('aria-expanded', 'false');
            }

            openNewsModal({
                action: btn.dataset.editUrl,
                title: btn.dataset.title,
                tag: btn.dataset.tag,
                body: btn.dataset.body,
                heading: 'Edit Dispatch',
                submitLabel: 'Save Changes',
            });
        });
    });

    newsOverlay.addEventListener('click', closeNewsModal);
    newsCloseBtn.addEventListener('click', closeNewsModal);
    newsCancelBtn.addEventListener('click', closeNewsModal);

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeNewsModal();
    });
}
