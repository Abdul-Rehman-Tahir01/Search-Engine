async function submitDocument(event) {
    event.preventDefault();

    const form = document.getElementById('add-document-form');
    console.log(form);
    // Collect form data
    const formData = {
        title: form.title.value,
        text: form.text.value,
        url: form.url.value,
        authors: form.authors.value,
        timestamp: form.timestamp.value,
        tags: form.tags.value
    };

    const successMessage = document.getElementById('success-message');
    successMessage.textContent = ''; // Clear previous messages

    try {
        // Send POST request to the backend
        const response = await fetch('/submit-document', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        // Check if the request was successful
        if (response.ok) {
            successMessage.style.display = 'block';
            successMessage.textContent = 'Document submitted successfully!';
            setTimeout(() => {
                window.location.href = '/'; // Redirect to the home page
            }, 1000);
        } else {
            const error = await response.json();
            alert(`Error: ${error.message}`);
        }
    } catch (err) {
        alert(`An error occurred: ${err.message}`);
    }
}
