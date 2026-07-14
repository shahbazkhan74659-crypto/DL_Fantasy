// CARD MENU — reusable three-dot dropdown
//
// One delegated listener handles every .card-menu on the page (present now or added later),
// so any future card using templates/_card_menu.html gets working open/close/outside-click/Escape
// behavior for free, with no per-page wiring beyond including the partial.
//
// CONFIRM MODAL — the [data-confirm] guard below is intentionally not scoped to .card-menu — any
// element anywhere on the page with a [data-confirm] attribute gets the same "are you sure?"
// behavior for free (e.g. the standalone delete button on the upload pages' "Already Uploaded"
// list, which isn't a dropdown menu at all). It pops the site-wide modal declared once in
// base.html rather than the browser's native window.confirm(), so the prompt matches the rest of
// the site's design instead of looking like an OS dialog. The element carrying [data-confirm] is
// expected to be a submit button inside a <form> — confirming re-submits that same form
// programmatically (form.submit(), which skips the button's own click handler, so this doesn't
// re-trigger the confirm prompt).

function closeAllCardMenus(except) {

    document.querySelectorAll('.card-menu.is-open').forEach((menu) => {

        if (menu === except) return;

        menu.classList.remove('is-open');

        const toggle = menu.querySelector('.card-menu-toggle');
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
    });
}

const confirmOverlay = document.querySelector('#confirm-modal-overlay');
const confirmModal = document.querySelector('#confirm-modal');
const confirmMessage = document.querySelector('#confirm-modal-message');
const confirmOkBtn = document.querySelector('#confirm-modal-ok');
const confirmCancelBtn = document.querySelector('#confirm-modal-cancel');

let pendingConfirmForm = null;

function openConfirmModal(message, form) {

    pendingConfirmForm = form;
    confirmMessage.textContent = message;

    confirmOverlay.classList.add('is-open');
    confirmModal.classList.add('is-open');
    confirmModal.setAttribute('aria-hidden', 'false');
}

function closeConfirmModal() {

    pendingConfirmForm = null;

    confirmOverlay.classList.remove('is-open');
    confirmModal.classList.remove('is-open');
    confirmModal.setAttribute('aria-hidden', 'true');
}

if (confirmModal) {

    confirmOverlay.addEventListener('click', closeConfirmModal);
    confirmCancelBtn.addEventListener('click', closeConfirmModal);

    confirmOkBtn.addEventListener('click', () => {

        const form = pendingConfirmForm;
        closeConfirmModal();

        if (form) form.submit();
    });

    window.addEventListener('keydown', (e) => {

        if (e.key === 'Escape' && confirmModal.classList.contains('is-open')) closeConfirmModal();
    });
}

document.addEventListener('click', (e) => {

    const toggle = e.target.closest('.card-menu-toggle');

    if (toggle) {

        e.preventDefault();
        e.stopPropagation();

        const menu = toggle.closest('.card-menu');
        const isOpen = menu.classList.contains('is-open');

        closeAllCardMenus();

        if (!isOpen) {
            menu.classList.add('is-open');
            toggle.setAttribute('aria-expanded', 'true');
        }

        return;
    }

    const confirmBtn = e.target.closest('[data-confirm]');

    if (confirmBtn) {

        e.preventDefault();

        const menu = confirmBtn.closest('.card-menu');
        if (menu) closeAllCardMenus();

        openConfirmModal(confirmBtn.dataset.confirm, confirmBtn.closest('form'));
        return;
    }

    if (!e.target.closest('.card-menu')) {
        closeAllCardMenus();
    }
});

window.addEventListener('keydown', (e) => {

    if (e.key === 'Escape') closeAllCardMenus();
});
