// EDIT PROFILE MODAL

const editProfileOverlay = document.querySelector('#edit-profile-overlay');
const editProfileModal = document.querySelector('#edit-profile-modal');
const editProfileBtn = document.querySelector('#edit-profile-btn');
const editProfileCloseBtn = document.querySelector('#edit-profile-close');
const editProfileCancelBtn = document.querySelector('#edit-profile-cancel');

function openEditProfileModal() {
    openModal(editProfileOverlay, editProfileModal);
}

function closeEditProfileModal() {
    closeModal(editProfileOverlay, editProfileModal);
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
