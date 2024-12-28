async function handleSearch(event) {
    event.preventDefault();

    const query = document.getElementById('search-query').value;
    const resultsContainer = document.getElementById('results-container');
    const loadingSpinner = document.getElementById('loading');
    const timingInfo = document.getElementById('timing-info');
    const messageContainer = document.getElementById('message-container');
    
    resultsContainer.innerHTML = '';  // Clear previous results
    timingInfo.textContent = '';  // Clear previous timing info
    messageContainer.textContent = '';  // Clear previous messages
    loadingSpinner.style.display = 'flex';  // Show loading spinner

    // Start the timer
    const startTime = performance.now(); 
    console.log('\nTime started.')
    try {
        const response = await fetch(`/search?query=${encodeURIComponent(query)}`);
        const data = await response.json();

        loadingSpinner.style.display = 'none';  // Hide loading spinner

        if (data.message) {
            messageContainer.textContent = data.message;
        }

        if (data.results && data.results.length > 0) {
            
            // Stop the timer
            const endTime = performance.now();
            const totalTime = endTime - startTime;
            console.log('Time ended. The results have been displayed.')
            
            // Display timing info
            timingInfo.textContent = `Results returned in ${totalTime.toFixed(2)} ms`;

            data.results.forEach(result => {
                const resultDiv = document.createElement('div');
                resultDiv.classList.add('result');
                
                resultDiv.innerHTML = `
                    <p><strong>Document ID:</strong> ${result.doc_id}</p>
                    <p><strong>Score:</strong> ${result.score}</p>
                    <p><strong>Title:</strong> ${result.title}</p>
                    <p><strong>URL:</strong> <a href="${result.url}" target="_blank">${result.url}</a></p>
                    <p><strong>Tags:</strong> ${result.tags}</p>
                    <p><strong>Authors:</strong> ${result.authors}</p>
                `;

                // Making the entire results div clickable
                resultDiv.onclick = () => {
                    window.open(result.url, '_blank');  // Opens the URL in a new tab
                };

                resultsContainer.appendChild(resultDiv);
            });
        } else {
            const noResultsMessage = document.createElement('p');
            noResultsMessage.textContent = 'No results found';
            noResultsMessage.classList.add('centered-error');  // Add styling
            resultsContainer.appendChild(noResultsMessage);        }

    } catch (error) {
        loadingSpinner.style.display = 'none';  // Hide loading spinner
        const errorMessage = document.createElement('p');
        errorMessage.textContent = 'There was an error while searching. Please try again.';
        errorMessage.classList.add('centered-error');  // Add styling
        resultsContainer.appendChild(errorMessage);    
    }
}
