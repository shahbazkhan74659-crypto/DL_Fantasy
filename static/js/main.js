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

window.addEventListener("scroll", () => {

    const scrollY =
    window.scrollY;

    parallaxElements.forEach((element) => {

        element.style.transform =
        `translateY(${scrollY * 0.2}px)`;

    });

});

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

