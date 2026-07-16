// ZOD-VALIDATED AUTH FORMS (login / signup)
//
// Progressive enhancement only: on invalid input this blocks the submit and
// shows inline errors. If this script fails to load, the form still posts to
// Django, which re-validates everything server-side (the only place account
// creation / auth actually happens) — see core/forms.py.

import { z } from '../vendor/zod.js';

const SCHEMAS = {
    login: z.object({
        username: z.string().min(1, 'Email is required.').email('Enter a valid email address.'),
        password: z.string().min(1, 'Password is required.'),
    }),

    signup: z.object({
        username: z.string()
            .min(1, 'Username is required.')
            .max(150, 'Username must be 150 characters or fewer.')
            .regex(/^[\w.@+\- ]+$/, 'Only letters, digits, spaces, and @/./+/-/_ are allowed.'),
        email: z.string()
            .min(1, 'Email is required.')
            .email('Enter a valid email address.'),
        password1: z.string()
            .min(8, 'Password must be at least 8 characters.')
            .refine((value) => !/^\d+$/.test(value), 'Password can\'t be entirely numeric.'),
        password2: z.string()
            .min(1, 'Please confirm your password.'),
    }).refine((data) => data.password1 === data.password2, {
        message: 'Passwords do not match.',
        path: ['password2'],
    }),
};

function showFieldError(form, field, message){

    const input =
    form.elements.namedItem(field);

    const errorEl =
    form.querySelector(`[data-field-error="${field}"]`);

    if(input) input.classList.add('is-invalid');
    if(errorEl) errorEl.textContent = message;
}

function clearFieldError(form, field){

    const input =
    form.elements.namedItem(field);

    const errorEl =
    form.querySelector(`[data-field-error="${field}"]`);

    if(input) input.classList.remove('is-invalid');
    if(errorEl) errorEl.textContent = '';
}

function clearAllErrors(form){

    form.querySelectorAll('[data-field-error]').forEach((el) => {
        el.textContent = '';
    });

    form.querySelectorAll('.auth-field').forEach((el) => {
        el.classList.remove('is-invalid');
    });
}

document.querySelectorAll('form[data-zod]').forEach((form) => {

    const schema =
    SCHEMAS[form.dataset.zod];

    if(!schema) return;

    form.setAttribute('novalidate', '');

    form.querySelectorAll('.auth-field').forEach((input) => {

        input.addEventListener('input', () => clearFieldError(form, input.name));
    });

    form.addEventListener('submit', (event) => {

        const data =
        Object.fromEntries(new FormData(form).entries());

        const result =
        schema.safeParse(data);

        clearAllErrors(form);

        if(!result.success){

            event.preventDefault();

            const firstInvalid = {};

            for(const issue of result.error.issues){

                const field = issue.path[0];

                if(field && !(field in firstInvalid)){

                    firstInvalid[field] = true;
                    showFieldError(form, field, issue.message);
                }
            }

            const firstField =
            Object.keys(firstInvalid)[0];

            const firstInput =
            firstField && form.elements.namedItem(firstField);

            if(firstInput) firstInput.focus();
        }
    });
});
