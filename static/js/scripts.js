document.addEventListener('DOMContentLoaded', function () {
    const signupForm = document.getElementById('signupForm');
    const loginForm = document.getElementById('loginForm');
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');

    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const fakeDomains = ['example.com', 'idontwanttogiveemail.com', 'fake.com'];
        const domain = email.split('@')[1];
        return re.test(email) && !fakeDomains.includes(domain);
    }

    function validateMobileNumber(mobileNumber) {
        const re = /^[1-9]{1}[0-9]{9}$/;
        return re.test(mobileNumber);
    }

    function validateForm(event, formType) {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = formType === 'signup' ? document.getElementById('confirm_password').value : null;
        const firstName = formType === 'signup' ? document.getElementById('first_name').value : null;
        const lastName = formType === 'signup' ? document.getElementById('last_name').value : null;
        const mobileNumber = formType === 'signup' ? document.getElementById('mobile_number').value : null;
        const collegeName = formType === 'signup' ? document.getElementById('college_name').value : null;
        const qualification = formType === 'signup' ? document.getElementById('qualification').value : null;
        const gender = formType === 'signup' ? document.querySelector('input[name="gender"]:checked') : null;

        if (formType === 'signup' && (!firstName || !lastName || !mobileNumber || !collegeName || !qualification || !gender)) {
            alert('All fields are required.');
            event.preventDefault();
            return;
        }

        if (!email || !validateEmail(email)) {
            alert('Please enter a valid email address.');
            event.preventDefault();
            return;
        }

        if (!password) {
            alert('Please enter a password.');
            event.preventDefault();
            return;
        }

        if (formType === 'signup' && password !== confirmPassword) {
            alert('Passwords do not match.');
            event.preventDefault();
            return;
        }

        if (formType === 'signup' && (!validateMobileNumber(mobileNumber))) {
            alert('Please enter a valid 10-digit mobile number.');
            event.preventDefault();
            return;
        }
    }

    if (signupForm) {
        signupForm.addEventListener('submit', function (event) {
            validateForm(event, 'signup');
        });
    }

    if (loginForm) {
        loginForm.addEventListener('submit', function (event) {
            validateForm(event, 'login');
        });
    }

    if (hamburger) {
        hamburger.addEventListener('click', function () {
            navMenu.classList.toggle('show');
        });
    }

});


