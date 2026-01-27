const sidebarMenu = document.getElementById("sidebarMenu");
const currentPath = window.location.pathname;

if (sidebarMenu) {
  sidebarMenu.querySelectorAll("a").forEach((link) => {
    const linkPath = link.pathname;

    // Check current path matches the link or is a sub-path (e.g., /blog/ matches /blog/article/1)
    // Exclude '/' to prevent the Home link from being active on every page
    if (
      currentPath === linkPath ||
      (linkPath !== "/" && currentPath.startsWith(linkPath + "/"))
    ) {
      link.classList.add("active-link");
    }
  });
}

// Global Search functionality
const searchForm = document.getElementById("siteSearchForm");
const searchInput = document.getElementById("siteSearchInput");
const searchModalEl = document.getElementById("searchModal");
let searchModal;

if (searchForm && searchInput && searchModalEl) {
  // Initialize Bootstrap Modal
  searchModal = new bootstrap.Modal(searchModalEl);
  const resultsBody = document.getElementById("searchResultsBody");

  const performSearch = (query) => {
    // Show a loading spinner immediately
    resultsBody.innerHTML = `
      <div class="d-flex justify-content-center">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    `;
    searchModal.show();

    fetch(`/?q=${encodeURIComponent(query)}`, {
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        resultsBody.innerHTML = ""; // Clear spinner

        if (data.results && data.results.length > 0) {
          const listGroup = document.createElement("div");
          listGroup.className = "list-group";

          data.results.forEach((item) => {
            const a = document.createElement("a");
            a.href = item.url;
            a.className = "list-group-item list-group-item-action";
            a.innerHTML = `
              <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1">${item.title}</h6>
                <small class="text-muted">${item.type}</small>
              </div>
            `;
            listGroup.appendChild(a);
          });
          resultsBody.appendChild(listGroup);
        } else {
          resultsBody.innerHTML =
            '<p class="text-center text-muted">No results found.</p>';
        }
      })
      .catch((err) => {
        console.error("Search error:", err);
        resultsBody.innerHTML =
          '<p class="text-center text-danger">An error occurred during search.</p>';
      });
  };

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault(); // Prevent form from submitting the traditional way
    const query = searchInput.value.trim();

    if (query.length < 2) {
      resultsBody.innerHTML =
        '<p class="text-center text-muted">Please enter at least 2 characters.</p>';
      searchModal.show();
      return;
    }

    performSearch(query);
  });
}
