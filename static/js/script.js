document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const queryInput = document.getElementById('queryInput');
    const searchButton = document.getElementById('searchButton');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const resultsContainer = document.getElementById('resultsContainer');
    const definitionContent = document.getElementById('definitionContent');
    const suggestionsGrid = document.getElementById('suggestionsGrid');
    const questionsList = document.getElementById('questionsList');
    const exampleQueries = document.querySelectorAll('.example-query');

    // Add event listeners
    searchButton.addEventListener('click', performSearch);
    queryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Example queries click handler
    exampleQueries.forEach(example => {
        example.addEventListener('click', function() {
            queryInput.value = this.textContent;
            performSearch();
        });
    });

    // Main search function
    function performSearch() {
        const query = queryInput.value.trim();
        
        if (!query) {
            showNotification('Please enter a search query');
            return;
        }

        // Show loading indicator
        loadingIndicator.classList.remove('hidden');
        resultsContainer.classList.add('hidden');
        
        // Call the API
        fetch('/api/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayResults(data, query);
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while fetching results');
        })
        .finally(() => {
            loadingIndicator.classList.add('hidden');
        });
    }

    // Display results function
    function displayResults(data, query) {
        // Clear previous results
        definitionContent.innerHTML = '';
        suggestionsGrid.innerHTML = '';
        questionsList.innerHTML = '';
        
        // Display definition
        definitionContent.textContent = data.definition || 'No definition available';
        
        // Display suggestions
        if (data.suggestions && data.suggestions.length > 0) {
            data.suggestions.forEach(suggestion => {
                const card = document.createElement('div');
                card.className = 'suggestion-card';
                
                const title = document.createElement('h3');
                title.textContent = suggestion.title;
                
                const description = document.createElement('p');
                description.textContent = suggestion.description;
                
                card.appendChild(title);
                card.appendChild(description);
                suggestionsGrid.appendChild(card);
            });
        } else {
            suggestionsGrid.innerHTML = '<p>No suggestions available</p>';
        }
        
        // Display related questions
        if (data.relatedQuestions && data.relatedQuestions.length > 0) {
            data.relatedQuestions.forEach(question => {
                const li = document.createElement('li');
                li.textContent = question;
                li.addEventListener('click', () => {
                    queryInput.value = question;
                    performSearch();
                });
                questionsList.appendChild(li);
            });
        } else {
            questionsList.innerHTML = '<p>No related questions available</p>';
        }
        
        // Show results container
        resultsContainer.classList.remove('hidden');
        
        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    // Notification helper
    function showNotification(message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        
        // Style the notification
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.left = '50%';
        notification.style.transform = 'translateX(-50%)';
        notification.style.backgroundColor = '#f44336';
        notification.style.color = 'white';
        notification.style.padding = '12px 24px';
        notification.style.borderRadius = '4px';
        notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        notification.style.zIndex = '1000';
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 500);
        }, 3000);
    }
});