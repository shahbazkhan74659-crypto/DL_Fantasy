// NAVBAR SCROLL EFFECT

window.addEventListener("scroll", () => {

    const navbar = document.querySelector(".navbar");

    if(window.scrollY > 50){

        navbar.classList.add("scrolled");

    } else {

        navbar.classList.remove("scrolled");
    }
});

// NAVBAR HEIGHT SYNC
//
// .navbar is position:fixed (always on screen), so it no longer reserves its own space in
// normal flow — body's padding-top (static/style.css) stands in for that space via the
// --navbar-h custom property. The navbar's real height isn't constant (the 900px breakpoint
// stacks it into multiple rows), so a ResizeObserver keeps the property correct across
// breakpoint changes and font-loading reflows, not just a one-time measurement at load.

const navbarForHeightSync = document.querySelector(".navbar");

if(navbarForHeightSync){

    const syncNavbarHeight = () => {

        document.documentElement.style.setProperty("--navbar-h", `${navbarForHeightSync.offsetHeight}px`);
    };

    syncNavbarHeight();

    new ResizeObserver(syncNavbarHeight).observe(navbarForHeightSync);
}

// PAGE-CONTENT-DEPENDENT EFFECTS
//
// Bundled into one re-runnable function because list-filters.js swaps
// main.page-content's innerHTML via AJAX (topic filters, pagination, in-page
// search) instead of a full page reload — anything that queried the DOM once
// at script-load time would go stale for cards/parallax elements that arrive
// after that swap, so this gets called again post-swap via window.initPageEffects().

const pageContent = document.querySelector(".page-content");

function initPageEffects() {

    // SCROLL REVEAL ANIMATION

    const cards = document.querySelectorAll(".archive-card");

    const observer = new IntersectionObserver((entries) => {

        entries.forEach((entry) => {

            if(entry.isIntersecting){

                entry.target.classList.add("show");
            }
        });

    }, {
        threshold:0.1
    });

    cards.forEach((card) => {

        observer.observe(card);

    });

    // CARD GLOW EFFECT

    cards.forEach((card) => {

        card.addEventListener("mousemove", (e) => {

            const rect = card.getBoundingClientRect();

            const x = e.clientX - rect.left;

            const y = e.clientY - rect.top;

            card.style.setProperty(
                "--x",
                `${x}px`
            );

            card.style.setProperty(
                "--y",
                `${y}px`
            );
        });

    });

    // PARALLAX HERO EFFECT

    const parallaxElements = document.querySelectorAll(".parallax");

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if(!prefersReducedMotion){

        parallaxHeroEffect.elements = parallaxElements;
    }

    // ACTIVE NAVBAR LINK

    const currentPath = window.location.pathname;

    const navItems = document.querySelectorAll(".nav-item");

    navItems.forEach((item) => {

        const itemPath = item.getAttribute("href");

        item.classList.toggle("active", currentPath === itemPath);

    });

    // CONTENT TRANSITION EFFECT

    const links = document.querySelectorAll("a");

    links.forEach((link) => {

        // Skip topic-filter chips, the order toggle, pagination links, and in-page search
        // boxes — list-filters.js handles those itself via a delegated listener, swapping
        // content in place instead of doing a full page navigation. Smart-back links are
        // skipped too: back-link.js calls history.back() on them, and scheduling
        // window.location.href on top of that races the two navigations.
        if(link.closest(".topic-filter, .order-toggle, .pagination, [data-smart-back]")){

            return;
        }

        link.addEventListener("click", (e) => {

            const href = link.getAttribute("href");

            if(
                href &&
                !href.startsWith("#") &&
                !href.startsWith("javascript")
            ){

                e.preventDefault();

                pageContent.classList.add("fade-out");

                setTimeout(() => {

                    window.location.href = href;

                }, 400);
            }
        });

    });

}

const parallaxHeroEffect = { elements: [] };

const prefersReducedMotionGlobal = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if(!prefersReducedMotionGlobal){

    window.addEventListener("scroll", () => {

        const scrollY = window.scrollY;

        parallaxHeroEffect.elements.forEach((element) => {

            element.style.transform = `translateY(${scrollY * 0.2}px)`;

        });

    });

}

initPageEffects();
window.initPageEffects = initPageEffects;

// READING PROGRESS BAR

window.addEventListener("scroll", () => {

    const scrollTop = document.documentElement.scrollTop;

    const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;

    const scrollPercent = (scrollTop / scrollHeight) * 100;

    document.querySelector(".progress-bar").style.width = `${scrollPercent}%`;
});

// RESET FADE-OUT ON BACK/FORWARD NAVIGATION
// (fixes pages restored from bfcache staying stuck at opacity:0)

window.addEventListener("pageshow", () => {

    pageContent.classList.remove("fade-out");

});

// PROFILE ICON FLOAT EFFECT

const profileCircle = document.querySelector(".profile-circle");

if(profileCircle){

    profileCircle.addEventListener("mouseenter", () => {

        profileCircle.style.transform = "translateY(-3px) scale(1.08)";

    });

    profileCircle.addEventListener("mouseleave", () => {

        profileCircle.style.transform = "translateY(0px) scale(1)";

    });

}

// SIDE DRAWER MENU

const menuToggle = document.querySelector(".menu-toggle");

const sideDrawer = document.querySelector("#side-drawer");

const drawerOverlay = document.querySelector("#drawer-overlay");

const drawerClose = document.querySelector(".drawer-close");

if(menuToggle && sideDrawer && drawerOverlay){

    const openDrawer = () => {

        sideDrawer.classList.add("is-open");
        drawerOverlay.classList.add("is-open");
        menuToggle.classList.add("is-open");
        menuToggle.setAttribute("aria-expanded", "true");
        sideDrawer.setAttribute("aria-hidden", "false");

    };

    const closeDrawer = () => {

        sideDrawer.classList.remove("is-open");
        drawerOverlay.classList.remove("is-open");
        menuToggle.classList.remove("is-open");
        menuToggle.setAttribute("aria-expanded", "false");
        sideDrawer.setAttribute("aria-hidden", "true");

    };

    menuToggle.addEventListener("click", () => {

        if(sideDrawer.classList.contains("is-open")){

            closeDrawer();

        } else {

            openDrawer();
        }

    });

    drawerOverlay.addEventListener("click", closeDrawer);

    if(drawerClose){

        drawerClose.addEventListener("click", closeDrawer);
    }

    window.addEventListener("keydown", (e) => {

        if(e.key === "Escape"){

            closeDrawer();
        }

    });

}

// LIVE CLOCK

const clockEl = document.querySelector("#clock");

if(clockEl){

    const updateClock = () => {

        clockEl.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    };

    updateClock();
    setInterval(updateClock, 1000);

}
