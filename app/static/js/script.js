console.log("Ay");

window.onload = function() {
    document.getElementById('addSourceButton').addEventListener('click', function() {
        document.getElementById('sourceInput').value = '';
        document.getElementById('modalMessage').textContent = '';
        document.getElementById('loadingSpinner').classList.add('d-none');
    });

    document.getElementById('addSourceSubmit').addEventListener('click', async function() {
        const sourceId = document.getElementById('sourceInput').value.trim();
        if (sourceId === '') {
            document.getElementById('modalMessage').textContent = 'Please enter a valid source ID.';
            return;
        }

        document.getElementById('loadingSpinner').classList.remove('d-none');
        document.getElementById('modalMessage').textContent = '';

        try {
            const response = await fetch('/api/add/' + sourceId, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();

            if (data.status === "success") {
                const modalMessage = document.getElementById('modalMessage');
                modalMessage.classList.add('text-success');
                modalMessage.classList.remove('text-danger');
                modalMessage.innerHTML = `${data.message} <br><a href="/view/${sourceId}" target="_blank">View Article</a>`;
            } else {
                const modalMessage = document.getElementById('modalMessage');
                modalMessage.textContent = 'Failed to add source. ' + data.message;
                modalMessage.classList.add('text-danger');
                modalMessage.classList.remove('text-success');
            }
        } catch (error) {
            const modalMessage = document.getElementById('modalMessage');
            modalMessage.textContent = 'An error occurred. Please notify an admin.';
            modalMessage.classList.add('text-danger');
            modalMessage.classList.remove('text-success');
        } finally {
            document.getElementById('loadingSpinner').classList.add('d-none');
        }
    });
};
