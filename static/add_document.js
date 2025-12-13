async function submitDocument(event) {
    event.preventDefault();

    const form = document.getElementById('add-document-form');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');

    successMessage.textContent = ''; // Clear previous messages
    errorMessage.textContent = ''; // Clear previous messages

    console.log(form);
    
    // Collect form data
    const formData = {
        title: form.title.value.trim(),
        text: form.text.value.trim(),
        url: form.url.value.trim(),
        authors: form.authors.value.trim(),
        timestamp: form.timestamp.value,
        tags: form.tags.value.trim()
    };

// =====================================================================================    
// Validation checks
const errors = [];

// Title: non-empty string
if (!formData.title) {
        errors.push('Title is required');
    } else if (formData.title.length > 200) {
        errors.push('Title must be 200 characters or less');
    }
    
    // Text: non-empty string, reasonable length
    if (!formData.text) {
        errors.push('Article text is required');
    } else if (formData.text.length < 5) {
        errors.push('Article text must be at least 5 characters');
    } else if (formData.text.length > 50000) {
        errors.push('Article text must be 50,000 characters or less');
    }
    
    // URL: valid format
    if (!formData.url) {
        errors.push('URL is required');
    } else {
        try {
            const urlObj = new URL(formData.url);
            if (!urlObj.protocol.match(/^https?:/)) {
                errors.push('URL must start with http:// or https://');
            }
        } catch {
            errors.push('Invalid URL format');
        }
    }

    // Authors: comma-separated, at least one
    if (!formData.authors) {
        errors.push('Authors are required');
    } else {
        const authorsList = formData.authors.split(',').map(a => a.trim()).filter(a => a);
        if (authorsList.length === 0) {
            errors.push('At least one author is required (comma-separated)');
        } else if (authorsList.length > 10) {
            errors.push('Maximum 10 authors allowed');
        }
    }
    
    // Timestamp: valid datetime-local format
    if (!formData.timestamp) {
        errors.push('Publication timestamp is required');
    } else {
        const timestamp = new Date(formData.timestamp);
        if (isNaN(timestamp.getTime())) {
            errors.push('Invalid timestamp format');
        }
    }

    // Tags: comma-separated, 1-8 tags
    if (!formData.tags) {
        errors.push('Tags are required');
    } else {
        const tagsList = formData.tags.split(',').map(t => t.trim()).filter(t => t);
        if (tagsList.length === 0) {
            errors.push('At least one tag is required (comma-separated)');
        } else if (tagsList.length > 15) {
            errors.push('Maximum 15 tags allowed');
        }
    }
    
    // If validation fails, show errors and stop
    if (errors.length > 0) {
        errorMessage.textContent = errors.join('\n');
        errorMessage.style.display = 'block';  
        form.parentNode.insertBefore(errorMessage, form.nextSibling);
        return; // Don't send to backend
    }
// =====================================================================================    

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
            errorMessage.textContent = `Server Error: ${error.message}`;
            form.parentNode.insertBefore(errorMessage, form.nextSibling);
        }
    } catch (err) {
        errorMessage.textContent = `Network Error: ${err.message}`;
        form.parentNode.insertBefore(errorMessage, form.nextSibling);
    }
}
