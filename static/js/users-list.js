// EDIT USER MODAL

const editOverlay = document.querySelector('#edit-user-overlay');
const editModal = document.querySelector('#edit-user-modal');
const editForm = document.querySelector('#edit-user-form');
const editUsernameInput = document.querySelector('#edit-username');
const editEmailInput = document.querySelector('#edit-email');
const editActiveInput = document.querySelector('#edit-active');
const editCloseBtn = document.querySelector('#edit-user-close');
const editCancelBtn = document.querySelector('#edit-user-cancel');

function openEditModal(button) {

    editForm.action = button.dataset.editUrl;
    editUsernameInput.value = button.dataset.username;
    editEmailInput.value = button.dataset.email;
    editActiveInput.checked = button.dataset.active === '1';

    openModal(editOverlay, editModal, editUsernameInput);
}

function closeEditModal() {
    closeModal(editOverlay, editModal);
}

if (editModal) {

    document.querySelectorAll('.edit-user-btn').forEach((btn) => {
        btn.addEventListener('click', () => openEditModal(btn));
    });

    editOverlay.addEventListener('click', closeEditModal);
    editCloseBtn.addEventListener('click', closeEditModal);
    editCancelBtn.addEventListener('click', closeEditModal);

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeEditModal();
    });
}

// Delete confirmation for .delete-user-form is handled globally by card-menu.js's
// [data-confirm] listener (site-wide custom modal instead of window.confirm()).
