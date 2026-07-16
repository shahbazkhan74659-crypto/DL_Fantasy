// SMART BACK LINK — delegated site-wide listener for any [data-smart-back] link, registered once
// in base.html (same pattern as card-menu.js/favourite.js/reading-list.js), so it already works
// on any current or future page that adds the attribute.
//
// Progressive enhancement: the link's href is always a real fallback destination (e.g. the
// category list or news list), so it still works with JS disabled. With JS, if this tab actually
// has a previous page in its history (window.history.length > 1), clicking goes there instead via
// history.back() — so "Back" returns to wherever the visitor really navigated from (Home, Search,
// Favourites, a category list, etc.) instead of always jumping to one hardcoded page.
document.addEventListener('click', (event) => {

    const link = event.target.closest('[data-smart-back]');
    if (!link) return;

    if (window.history.length > 1) {
        event.preventDefault();
        window.history.back();
    }
});
