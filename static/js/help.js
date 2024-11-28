document.getElementById('helpForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission

    // Get input values
    const name = document.getElementById('name').value.trim();
    const email = document.getElementById('email').value.trim();
    const phone = document.getElementById('phone').value.trim();
    const subject = document.getElementById('subject').value.trim();
    const content = document.getElementById('content').value.trim();

    // Regular expression for validating email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    // Regular expression for validating phone numbers (adjust as necessary)
    const phoneRegex = /^\d{10}$/; // Assuming a 10-digit phone number

    // Validate inputs
    if (!name || !email || !phone || !subject || !content) {
        alert('Please fill in all fields.');
        return;
    }
    if (!emailRegex.test(email)) {
        alert('Please enter a valid email address.');
        return;
    }
    if (!phoneRegex.test(phone)) {
        alert('Please enter a valid 10-digit phone number.');
        return;
    }

    // If validation passes, submit the form via AJAX
    const helpRequest = {
        name,
        email,
        phone,
        subject,
        content
    };

    fetch('/help', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(helpRequest)
    })
    .then(response => {
        if (response.ok) {
            alert('Help request submitted successfully!');
            document.getElementById('helpForm').reset(); // Reset form fields
        } else {
            alert('Error submitting help request. Please try again later.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error submitting help request. Please try again later.');
    });
});
