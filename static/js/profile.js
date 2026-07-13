// EDIT PROFILE MODAL

const editProfileOverlay = document.querySelector('#edit-profile-overlay');
const editProfileModal = document.querySelector('#edit-profile-modal');
const editProfileBtn = document.querySelector('#edit-profile-btn');
const editProfileCloseBtn = document.querySelector('#edit-profile-close');
const editProfileCancelBtn = document.querySelector('#edit-profile-cancel');

function openEditProfileModal() {

    editProfileOverlay.classList.add('is-open');
    editProfileModal.classList.add('is-open');
    editProfileModal.setAttribute('aria-hidden', 'false');
}

function closeEditProfileModal() {

    editProfileOverlay.classList.remove('is-open');
    editProfileModal.classList.remove('is-open');
    editProfileModal.setAttribute('aria-hidden', 'true');
}

if (editProfileModal) {

    if (editProfileBtn) editProfileBtn.addEventListener('click', openEditProfileModal);

    editProfileOverlay.addEventListener('click', closeEditProfileModal);
    editProfileCloseBtn.addEventListener('click', closeEditProfileModal);
    editProfileCancelBtn.addEventListener('click', closeEditProfileModal);

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeEditProfileModal();
    });
}
