document.addEventListener('DOMContentLoaded', function() {
  // Set current year in footer
  document.getElementById('year').textContent = new Date().getFullYear();
  
  // Initialize the scroll reveal effect
  initScrollReveal();
  
  // Initialize the publications fetch
  fetchPublications();
});

/**
 * Initialize scroll reveal animations
 */
function initScrollReveal() {
  // Fade in header elements with a delay
  const fadeInElements = document.querySelectorAll('.fade-in');
  fadeInElements.forEach((el, index) => {
    el.style.animationDelay = `${0.2 * index}s`;
  });
  
  // Reveal sections when scrolled into view
  const sections = document.querySelectorAll('.section-fade');
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.15
  });
  
  sections.forEach(section => {
    observer.observe(section);
  });
}

/**
 * Fetch publications from Google Scholar API
 * Using Serpapi's publicly available Google Scholar API
 */
function fetchPublications() {
  const scholarId = 'SC5NdrAAAAAJ';
  const publicationsContainer = document.querySelector('.publications-list');
  const loadingElement = document.querySelector('.publications-loading');
  const errorElement = document.querySelector('.publications-error');
  const fallbackElement = document.querySelector('.publications-fallback');
  
  // For GitHub Pages, we'll use a pre-generated JSON file approach instead of direct API calls
  // This simulates fetching from an API but actually uses local data that you would update periodically
  
  // In a real implementation, you'd have a GitHub Action workflow that periodically:
  // 1. Fetches data from Google Scholar 
  // 2. Generates a publications.json file
  // 3. Commits it to your repository
  
  // Use our local publications.json file
  const publicationsUrl = 'publications.json';
  
  fetch(publicationsUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      // Process the publications from our JSON file
      const publications = data.publications || [];
      
      if (publications.length === 0) {
        throw new Error('No publications found');
      }
      
      // Clear loading indicator
      loadingElement.style.display = 'none';
      
      // Sort publications by year (descending) and title (ascending)
      const sortedPublications = publications.sort((a, b) => {
        // First sort by year descending
        if (b.year !== a.year) {
          return b.year - a.year;
        }
        // If years are equal, sort by title ascending
        return a.title.localeCompare(b.title);
      });

      // Process each publication
      sortedPublications.forEach(pub => {
        const publicationEl = document.createElement('div');
        publicationEl.className = 'publication';
        publicationEl.innerHTML = `
          <p class="publication-title">${pub.title}</p>
          <p class="publication-authors">${pub.authors}</p>
          <p class="publication-venue">${pub.venue} ${pub.year ? '(' + pub.year + ')' : ''}</p>
          <a href="${pub.link}" target="_blank">View Publication</a>
        `;
        
        publicationsContainer.appendChild(publicationEl);
      });
    })
    .catch(error => {
      console.error('Error fetching publications:', error);
      
      // Show fallback content instead
      loadingElement.style.display = 'none';
      errorElement.style.display = 'block';
      fallbackElement.style.display = 'grid';
    });
}