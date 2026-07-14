// LIST FILTERS — AJAX-swap topic filters, pagination, and in-page search
//
// Topic-filter chips (.topic-filter), pager links (.pagination), and in-page
// search boxes (form.search-box, used on the Search and God Valley Chapters
// pages) all just re-filter the same list view with a new query string — they
// don't need a full browser navigation/reload to do that. This delegated
// listener intercepts those three controls specifically (main.js's own
// link-click handler skips them for exactly this reason) and instead fetches
// the target URL, swaps main.page-content's innerHTML in place, and updates
// the URL via history.pushState. Every other link on the site still does a
// normal full navigation, unchanged.

const FILTER_LINK_SELECTOR = ".topic-filter a, .pagination a";
const SEARCH_FORM_SELECTOR = "form.search-box";

function softNavigate(url, push) {

    const pageContent =
    document.querySelector(".page-content");

    if(!pageContent){

        window.location.href = url;
        return;
    }

    pageContent.classList.add("fade-out");

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

                const doc =
                new DOMParser().parseFromString(html, "text/html");

                const newMain =
                doc.querySelector("main.page-content");

                if(!newMain){

                    throw new Error("Soft navigation failed: no main.page-content in response");
                }

                pageContent.innerHTML = newMain.innerHTML;
                document.title = doc.title;

                if(push){

                    history.pushState({ softNav: true }, "", finalUrl);
                }

                pageContent.classList.remove("fade-out");

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

    const link =
    e.target.closest(FILTER_LINK_SELECTOR);

    if(!link) return;

    const href =
    link.getAttribute("href");

    if(!href) return;

    e.preventDefault();

    softNavigate(href, true);

});

document.addEventListener("submit", (e) => {

    const form =
    e.target.closest(SEARCH_FORM_SELECTOR);

    if(!form) return;

    e.preventDefault();

    const params =
    new URLSearchParams(new FormData(form));

    const url =
    `${form.getAttribute("action")}?${params.toString()}`;

    softNavigate(url, true);

});

window.addEventListener("popstate", () => {

    softNavigate(window.location.href, false);

});
