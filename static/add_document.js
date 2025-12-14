async function submitDocument(event) {
    event.preventDefault();

    const form = document.getElementById('add-document-form');
    const successMessage = document.getElementById('success-message');
    const errorMessage = document.getElementById('error-message');

    // Clear previous messages
    successMessage.textContent = ''; 
    successMessage.style.display = 'none';
    errorMessage.textContent = ''; 
    errorMessage.style.display = 'none';

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
        errorMessage.innerHTML = errors.join('<br>');
        errorMessage.style.display = 'block';  
        return; // Don't send to backend
    }
// =====================================================================================    

    // Show loading spinner
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.id = 'loading-spinner';
    loadingDiv.innerHTML = '<div class="spinner"></div><p style="color: white; margin-top: 10px;">Submitting document...</p>';
    form.appendChild(loadingDiv);

    // Disable submit button
    const submitButton = form.querySelector('.submit-button');
    submitButton.disabled = true;

    try {
        console.log('Sending data:', formData);
        // Send POST request to the backend
        const response = await fetch('/submit-document', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        // Remove loading spinner
        const spinner = document.getElementById('loading-spinner');
        if (spinner) spinner.remove();
        submitButton.disabled = false;

        console.log('Response status:', response.status);
        const responseData = await response.json();
        console.log('Response data:', responseData);

        // Check if the request was successful
        if (response.ok) {
            successMessage.style.display = 'block';
            successMessage.textContent = 'Document submitted successfully! Redirecting...';
            form.reset();
            setTimeout(() => {
                window.location.href = '/'; // Redirect to the home page
            }, 1500);
        } else {
            errorMessage.textContent = `Error: ${responseData.message || 'Unknown error'}`;
            errorMessage.style.display = 'block';
        }
    } catch (err) {
        // Remove loading spinner
        const spinner = document.getElementById('loading-spinner');
        if (spinner) spinner.remove();
        submitButton.disabled = false;

        console.error('Network error:', err);
        errorMessage.textContent = `Network Error: ${err.message}`;
        errorMessage.style.display = 'block';
    }
}
