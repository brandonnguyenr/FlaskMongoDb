document.addEventListener("DOMContentLoaded", function() {
    // Fetch images from the 'uploads' folder
    fetchImages();
});

function fetchImages() {
    // Path to the 'uploads' folder
    const folderPath = 'uploads/uploads/';

    // Fetch images from the folder
    fetch(folderPath)
        .then(response => response.text())
        .then(html => {
            // Create a temporary element to parse the HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Select all <a> tags (links to images) in the response
            const links = Array.from(doc.querySelectorAll('a'));

            // Filter out links to directories and hidden files
            const imageLinks = links
                .map(link => link.getAttribute('href'))
                .filter(link => !link.startsWith('.') && !link.endsWith('/'));

            // Display images on the page
            displayImages(imageLinks);
        })
        .catch(error => console.error('Error fetching images:', error));
}

function displayImages(imageLinks) {
    const container = document.getElementById('image-container');

    // Clear previous content
    container.innerHTML = '';

    // Add images to the container
    imageLinks.forEach(link => {
        const img = document.createElement('img');
        img.src = 'uploads/uploads/' + link;
        img.alt = link;
        img.classList.add('uploaded-image');
        container.appendChild(img);
    });
}
