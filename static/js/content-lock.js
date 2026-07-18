// CONTENT LOCK — anonymous visitors clicking the favourite/reading-list/download icons on a
// gated chapter/essay land on the login card instead of navigating straight to /login/.
//
// One delegated listener handles every `.js-scroll-to-lock` link (works without JS too, since
// each one is a real `href="#content-lock"` anchor — this just upgrades the jump to a smooth,
// centered scroll). The Log In button's pop only starts once the scroll has actually settled —
// firing both at once made it look like the whole card was jumping mid-scroll.

const SCROLL_SETTLE_FALLBACK_MS = 700; // used on browsers without the 'scrollend' event

document.addEventListener('click', (e) => {

    const trigger = e.target.closest('.js-scroll-to-lock');

    if (!trigger) return;

    const lock = document.getElementById('content-lock');

    if (!lock) return;

    e.preventDefault();

    const loginBtn = document.getElementById('content-lock-login-btn');

    const playPop = () => {
        if (!loginBtn) return;
        loginBtn.classList.remove('pop');
        void loginBtn.offsetWidth; // restarts the CSS animation on repeat clicks
        loginBtn.classList.add('pop');
    };

    if ('onscrollend' in window) {
        window.addEventListener('scrollend', playPop, { once: true });
    } else {
        setTimeout(playPop, SCROLL_SETTLE_FALLBACK_MS);
    }

    lock.scrollIntoView({ behavior: 'smooth', block: 'center' });
});
