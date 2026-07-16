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
// expected to be a submit button inside a <form> — confirming re-submits via
// form.requestSubmit(button), not form.submit(): some [data-confirm] buttons (e.g. the cover-image
// delete button on the upload edit page) are a plain submit button with its own
// formaction/formmethod inside the page's main <form>, rather than a separate nested <form> of
// their own (nested <form> elements are invalid HTML and get silently flattened into the outer
// form by the browser's parser). form.submit() always ignores a submitter's formaction/formmethod
// override and just posts to the form's own default action; requestSubmit(button) submits exactly
// as if that button had been clicked, honoring its override. Neither method dispatches a 'click'
// event on the button, so this doesn't re-trigger our own delegated click listener below either
// way.

// GENERIC MODAL OPEN/CLOSE — shared by the confirm modal below and by any page-specific modal
// (profile.js, users-list.js, news.js). Site-wide since card-menu.js already loads on every page
// ahead of any per-page `extra_js` script, so these two functions are available as plain globals
// wherever a page needs its own overlay/modal pair opened or closed — only the feature-specific
// field-population logic (which fields to fill, which button to focus) stays local to each page's
// own script.

function openModal(overlay, modal, focusEl) {

    overlay.classList.add('is-open');
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');

    if (focusEl) focusEl.focus();
}

function closeModal(overlay, modal) {

    overlay.classList.remove('is-open');
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
}

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
let pendingConfirmSubmitter = null;

function openConfirmModal(message, form, submitter) {

    pendingConfirmForm = form;
    pendingConfirmSubmitter = submitter;
    confirmMessage.textContent = message;

    openModal(confirmOverlay, confirmModal);
}

function closeConfirmModal() {

    pendingConfirmForm = null;
    pendingConfirmSubmitter = null;

    closeModal(confirmOverlay, confirmModal);
}

if (confirmModal) {

    confirmOverlay.addEventListener('click', closeConfirmModal);
    confirmCancelBtn.addEventListener('click', closeConfirmModal);

    confirmOkBtn.addEventListener('click', () => {

        const form = pendingConfirmForm;
        const submitter = pendingConfirmSubmitter;
        closeConfirmModal();

        if (!form) return;

        if (submitter && form.requestSubmit) {
            form.requestSubmit(submitter);
        } else {
            form.submit();
        }
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

        openConfirmModal(confirmBtn.dataset.confirm, confirmBtn.closest('form'), confirmBtn);
        return;
    }

    if (!e.target.closest('.card-menu')) {
        closeAllCardMenus();
    }
});

window.addEventListener('keydown', (e) => {

    if (e.key === 'Escape') closeAllCardMenus();
});
