// LIST FILTERS — AJAX-swap topic filters, the order toggle, pagination, and in-page search
//
// Topic-filter chips (.topic-filter), the newest/oldest order toggle (.order-toggle), pager
// links (.pagination), and in-page search boxes (form.search-box, used on the Search and God
// Valley Chapters pages) all just re-filter the same list view with a new query string — they
// don't need a full browser navigation/reload to do that. This delegated listener intercepts
// those controls specifically (main.js's own link-click handler skips them for exactly this
// reason) and instead fetches the target URL and swaps content in place, updating the URL via
// history.pushState. Every other link on the site (including navbar links) still does a normal
// full navigation with the whole-page fade, unchanged.
//
// Pages that wrap their filter controls + card grid + pagination in a
// #list-panel, with the grid itself further wrapped in #card-grid-wrap
// (Writings, God Valley Chapters), only fade the card grid — the hero above
// #list-panel, and the filter controls/pagination inside it (the toggle,
// its checkbox icon, the active-topic label), update instantly with no fade.
// Pages without that structure (Search, Favourites, ...) fall back to
// fading/swapping the whole main.page-content, as before.

const FILTER_LINK_SELECTOR = ".topic-filter a, .order-toggle, .pagination a";
const SEARCH_FORM_SELECTOR = "form.search-box";

function swapOuterHTML(current, next) {

    if(current && next){
        current.outerHTML = next.outerHTML;
    } else if(current && !next){
        current.remove();
    } else if(!current && next){
        return next.outerHTML; // caller inserts this next to a still-live anchor node
    }

    return null;
}

function softNavigate(url, push) {

    const pageContent = document.querySelector(".page-content");

    if(!pageContent){

        window.location.href = url;
        return;
    }

    const listPanel = pageContent.querySelector("#list-panel");
    const cardGridWrap = listPanel ? listPanel.querySelector("#card-grid-wrap") : null;
    const fadeTarget = cardGridWrap || listPanel || pageContent;

    fadeTarget.classList.add("fade-out");

    setTimeout(() => {

        fetch(url)
            .then((response) => {

                if(!response.ok){

                    throw new Error("Soft navigation failed: " + response.status);
                }

                // response.url reflects where fetch actually landed after following
                // any redirect (e.g. a login-required page redirecting a lapsed
                // session to /login/) — that's what belongs in the address bar,
                // not the originally-requested url.
                return response.text().then((html) => [html, response.url]);

            })
            .then(([html, finalUrl]) => {

                const doc = new DOMParser().parseFromString(html, "text/html");

                const newMain = doc.querySelector("main.page-content");

                if(!newMain){

                    throw new Error("Soft navigation failed: no main.page-content in response");
                }

                const newListPanel = newMain.querySelector("#list-panel");

                if(listPanel && cardGridWrap && newListPanel){

                    const controls = listPanel.querySelector(".list-controls");
                    const newControls = newListPanel.querySelector(".list-controls");
                    swapOuterHTML(controls, newControls);

                    const newCardGridWrap = newListPanel.querySelector("#card-grid-wrap");
                    if(newCardGridWrap) cardGridWrap.innerHTML = newCardGridWrap.innerHTML;

                    const pagination = listPanel.querySelector(".pagination");
                    const newPagination = newListPanel.querySelector(".pagination");
                    const insertHTML = swapOuterHTML(pagination, newPagination);
                    if(insertHTML) cardGridWrap.insertAdjacentHTML("afterend", insertHTML);

                } else if(listPanel){

                    listPanel.innerHTML = newListPanel ? newListPanel.innerHTML : newMain.innerHTML;

                } else {

                    pageContent.innerHTML = newMain.innerHTML;
                }

                document.title = doc.title;

                if(push){

                    history.pushState({ softNav: true }, "", finalUrl);
                }

                fadeTarget.classList.remove("fade-out");

                window.scrollTo({ top: 0, behavior: "smooth" });

                if(window.initPageEffects){

                    window.initPageEffects();
                }

            })
            .catch(() => {

                window.location.href = url;

            });

    }, 400);

}

document.addEventListener("click", (e) => {

    const link = e.target.closest(FILTER_LINK_SELECTOR);

    if(!link) return;

    const href = link.getAttribute("href");

    if(!href) return;

    e.preventDefault();

    softNavigate(href, true);

});

document.addEventListener("submit", (e) => {

    const form = e.target.closest(SEARCH_FORM_SELECTOR);

    if(!form) return;

    e.preventDefault();

    const params = new URLSearchParams(new FormData(form));

    const url = `${form.getAttribute("action")}?${params.toString()}`;

    softNavigate(url, true);

});

window.addEventListener("popstate", () => {

    softNavigate(window.location.href, false);

});
