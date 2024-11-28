document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('settingsForm');

    form.addEventListener('submit', function (event) {
        // Clear previous errors
        clearErrors();

        // Validate form fields
        const firstName = document.getElementById('first_name');
        const lastName = document.getElementById('last_name');
        const email = document.getElementById('email');
        const mobile = document.getElementById('mobile');
        const college = document.getElementById('college');
        const qualification = document.getElementById('qualification');

        let isValid = true;

        // Validate first name and last name
        if (!isValidName(firstName.value)) {
            showError(firstName, 'First name must contain only alphabets.');
            isValid = false;
        }

        if (!isValidName(lastName.value)) {
            showError(lastName, 'Last name must contain only alphabets.');
            isValid = false;
        }

        // Validate email
        if (!isValidEmail(email.value)) {
            showError(email, 'Invalid email format.');
            isValid = false;
        }

        // Validate mobile number
        if (!isValidMobile(mobile.value)) {
            showError(mobile, 'Mobile number must be a 10-digit number.');
            isValid = false;
        }

        // Prevent form submission if validation fails
        if (!isValid) {
            event.preventDefault();
        }
    });

    function clearErrors() {
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(function (message) {
            message.remove();
        });

        const errorFields = document.querySelectorAll('.error');
        errorFields.forEach(function (field) {
            field.classList.remove('error');
        });
    }

    function showError(element, message) {
        element.classList.add('error');
        const errorMessage = document.createElement('div');
        errorMessage.className = 'error-message';
        errorMessage.textContent = message;
        element.parentElement.appendChild(errorMessage);
    }

    function isValidName(name) {
        return /^[A-Za-z]+$/.test(name);
    }

    function isValidEmail(email) {
        const emailPattern = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
        return emailPattern.test(email);
    }

    function isValidMobile(mobile) {
        return /^\d{10}$/.test(mobile);
    }
});
