
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('.header__search-form');
    const searchInput = document.querySelector('.header__search-input');
    const searchHistoryList = document.querySelector('.header__search-history-list');

    searchForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const searchTerm = searchInput.value.trim();

        if (searchTerm) {
            fetch(`?q=${encodeURIComponent(searchTerm)}`)
                .then(response => response.json())
                .then(data => {
                    displaySearchResults(data);
                })
                .catch(error => {
                    console.error('Error fetching search results:', error);
                });
        }
    });

    function displaySearchResults(results) {
        searchHistoryList.innerHTML = '';
        if (results.length > 0) {
            const listItem = document.createElement('li');
            listItem.classList.add('header__search-history-item');
            listItem.textContent = results[0].name;
            searchHistoryList.appendChild(listItem);
        } else {
            const listItem = document.createElement('li');
            listItem.classList.add('header__search-history-item');
            listItem.textContent = 'No results found';
            searchHistoryList.appendChild(listItem);
        }
    }
});




var slideIndex = 0;
showSlides();

function showSlides() {
    var i;
    var slides = document.getElementsByClassName("mySlides");

for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";
}

slideIndex++;
if (slideIndex > slides.length) {slideIndex = 1}
slides[slideIndex-1].style.display = "block";  

setTimeout(showSlides, 3500);
}
