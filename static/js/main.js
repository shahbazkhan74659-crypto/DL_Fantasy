// NAVBAR SCROLL EFFECT

window.addEventListener("scroll", () => {

    const navbar =
    document.querySelector(".navbar");

    if(window.scrollY > 50){

        navbar.classList.add("scrolled");

    } else {

        navbar.classList.remove("scrolled");
    }
});

// SCROLL REVEAL ANIMATION

const cards =
document.querySelectorAll(".archive-card");

const observer =
new IntersectionObserver((entries) => {

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

const archiveCards =
document.querySelectorAll(".archive-card");

archiveCards.forEach((card) => {

    card.addEventListener("mousemove", (e) => {

        const rect =
        card.getBoundingClientRect();

        const x =
        e.clientX - rect.left;

        const y =
        e.clientY - rect.top;

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

// READING PROGRESS BAR

window.addEventListener("scroll", () => {

    const scrollTop =
        document.documentElement.scrollTop;

    const scrollHeight =
        document.documentElement.scrollHeight -
        document.documentElement.clientHeight;

    const scrollPercent =
        (scrollTop / scrollHeight) * 100;

    document.querySelector(".progress-bar")
        .style.width =
        `${scrollPercent}%`;
});

// CONTENT TRANSITION EFFECT

const pageContent =
document.querySelector(".page-content");

const links =
document.querySelectorAll("a");

links.forEach((link) => {

    link.addEventListener("click", (e) => {

        const href =
        link.getAttribute("href");

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

// RESET FADE-OUT ON BACK/FORWARD NAVIGATION
// (fixes pages restored from bfcache staying stuck at opacity:0)

window.addEventListener("pageshow", () => {

    pageContent.classList.remove("fade-out");

});

// PARALLAX HERO EFFECT

const parallaxElements =
document.querySelectorAll(".parallax");

const prefersReducedMotion =
window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if(!prefersReducedMotion){

    window.addEventListener("scroll", () => {

        const scrollY =
        window.scrollY;

        parallaxElements.forEach((element) => {

            element.style.transform =
            `translateY(${scrollY * 0.2}px)`;

        });

    });

}

// ACTIVE NAVBAR LINK

const currentPath =
window.location.pathname;

const navItems =
document.querySelectorAll(".nav-item");

navItems.forEach((item) => {

    const itemPath =
    item.getAttribute("href");

    if(currentPath === itemPath){

        item.classList.add("active");
    }

});

// PROFILE ICON FLOAT EFFECT

const profileCircle =
document.querySelector(".profile-circle");

if(profileCircle){

    profileCircle.addEventListener("mouseenter", () => {

        profileCircle.style.transform =
        "translateY(-3px) scale(1.08)";

    });

    profileCircle.addEventListener("mouseleave", () => {

        profileCircle.style.transform =
        "translateY(0px) scale(1)";

    });

}

// SIDE DRAWER MENU

const menuToggle =
document.querySelector(".menu-toggle");

const sideDrawer =
document.querySelector("#side-drawer");

const drawerOverlay =
document.querySelector("#drawer-overlay");

const drawerClose =
document.querySelector(".drawer-close");

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

const clockEl =
document.querySelector("#clock");

if(clockEl){

    const updateClock = () => {

        clockEl.textContent =
        new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    };

    updateClock();
    setInterval(updateClock, 1000);

}

