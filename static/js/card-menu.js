// CARD MENU — reusable three-dot dropdown
//
// One delegated listener handles every .card-menu on the page (present now or added later),
// so any future card using templates/_card_menu.html gets working open/close/outside-click/Escape
// behavior for free, with no per-page wiring beyond including the partial.

function closeAllCardMenus(except) {

    document.querySelectorAll('.card-menu.is-open').forEach((menu) => {

        if (menu === except) return;

        menu.classList.remove('is-open');

        const toggle = menu.querySelector('.card-menu-toggle');
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
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

    const confirmBtn = e.target.closest('.card-menu [data-confirm]');

    if (confirmBtn && !window.confirm(confirmBtn.dataset.confirm)) {

        e.preventDefault();
        return;
    }

    if (!e.target.closest('.card-menu')) {
        closeAllCardMenus();
    }
});

window.addEventListener('keydown', (e) => {

    if (e.key === 'Escape') closeAllCardMenus();
});
