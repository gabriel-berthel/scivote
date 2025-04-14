let filteredData = [];

function fetchData(event) {
    const searchBar = document.getElementById('searchBar');
    const loadingText = document.getElementById('loadingText');

    searchBar.disabled = true;
    loadingText.style.display = 'block';

    const searchText = searchBar.value.toLowerCase();
    const categorySelect = document.getElementById('category_filter');
    const selectedCategory = categorySelect.value;
    const top_k_select = document.getElementById('numResultsSelect');
    const selected_k = top_k_select.value;

    const payload = {
        query: searchText,
        category: selectedCategory,
        top_k: selected_k
    };

    fetch('/api/search/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "error") {
            throw new Error(data.detail);
        }
        if (data.status === "success") {
            filteredData = data.results;
            filterResults();
        } else {
            console.error("API response is not in the expected format:", data);
            document.getElementById('errorMessage').textContent = `Error: API response is not in the expected format.`;
            showErrorModal();
        }
    })
    .catch(error => {
        console.error("Error fetching data:", error.message);
        document.getElementById('errorMessage').textContent = `Error: ${error.message}`;
        showErrorModal();
    })
    .finally(() => {
        searchBar.disabled = false;
        loadingText.style.display = 'none';
    });
}

function showErrorModal() {
    var myModal = new bootstrap.Modal(document.getElementById('errorModal'))
    myModal.show();
}

function closeModal() {
    const myModal = new bootstrap.Modal(document.getElementById('errorModal'));
    myModal.hide();
    document.getElementById('errorMessage').textContent = '';
}

// Function to filter results based on sliders
function filterResults() {
    const baseScoreWeight = parseFloat(document.getElementById('baseScoreWeightSlider').value);
    const recencyWeight = parseFloat(document.getElementById('recencySlider').value);
    const authorityWeight = parseFloat(document.getElementById('authoritySlider').value);
    const truthworthinessWeight = parseFloat(document.getElementById('truthworthinessSlider').value);
    const sentimentWeight = parseFloat(document.getElementById('sentimentSlider').value);
    const concisenessWeight = parseFloat(document.getElementById('concisenessSlider').value);
    const readabilityWeight = parseFloat(document.getElementById('readabilitySlider').value);
    const transparencyWeight = parseFloat(document.getElementById('transparencySlider').value);
    const numResults = parseInt(document.getElementById('numResultsSelect').value, 10);

    // Update slider values on UI
    document.getElementById('baseScoreWeightValue').textContent = baseScoreWeight;
    document.getElementById('recencyValue').textContent = recencyWeight;
    document.getElementById('authorityValue').textContent = authorityWeight;
    document.getElementById('truthworthinessValue').textContent = truthworthinessWeight;
    document.getElementById('sentimentValue').textContent = sentimentWeight;
    document.getElementById('concisenessValue').textContent = concisenessWeight;
    document.getElementById('readabilityValue').textContent = readabilityWeight;
    document.getElementById('transparencyValue').textContent = transparencyWeight;

    filteredData.forEach(item => {
        item.finalScore = calculateFinalScore(item, baseScoreWeight, recencyWeight, authorityWeight, truthworthinessWeight, sentimentWeight, concisenessWeight, readabilityWeight, transparencyWeight);
    });

    filteredData.sort((a, b) => b.finalScore - a.finalScore);
    displayResults(filteredData.slice(0, numResults));
}

function displayResults(results) {
    const resultContainer = document.getElementById('resultContainer');
    resultContainer.innerHTML = '';

    if (results.length === 0) {
        resultContainer.innerHTML = '<p>No results found.</p>';
    } else {
        results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.classList.add('card', 'mb-3');
            resultItem.innerHTML = `
                <div class="card-body">
                <h5 class="card-title"><a href="/view/${item.id}">${item.title}</a></h5>
                <p class="card-text">${item.abstract}</p>
                <p><strong>Final Score:</strong> ${item.finalScore.toFixed(2)}</p>
                </div>
            `;
            resultContainer.appendChild(resultItem);
        });
    }
}

searchBar.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
	event.preventDefault();
        fetchData(event);
    }
});

searchButton.addEventListener('click', function(event) {
    event.preventDefault();
    fetchData(event);
});


function calculateFinalScore(item, baseScoreWeight, recencyWeight, authorityWeight, truthworthinessWeight, sentimentWeight, concisenessWeight, readabilityWeight, transparencyWeight) {
    return (
        (item.baseScore * baseScoreWeight) +
        (item.recency * recencyWeight) +
        (item.authority * authorityWeight) +
        (item.truthworthiness * truthworthinessWeight) +
        (item.sentiment * sentimentWeight) +
        (item.conciseness * concisenessWeight) +
        (item.readability * readabilityWeight) +
        (item.transparency * transparencyWeight)
    );
}
