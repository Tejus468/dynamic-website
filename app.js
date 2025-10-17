// Theme Management
const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');
const html = document.documentElement;

function updateThemeIcon(theme) {
    if (themeIcon) {
        themeIcon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }
}

if (themeToggle && html) {
    const savedTheme = localStorage.getItem('cryptoTheme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = (currentTheme === 'light') ? 'dark' : 'light';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('cryptoTheme', newTheme);
        updateThemeIcon(newTheme);
    });
}

// --- Advanced Search and Filter ---
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function () {
        filterTable();
    });
}

const sortBySelect = document.getElementById('sortBy');
if (sortBySelect) {
    sortBySelect.addEventListener('change', function () {
        sortTable(this.value);
    });
}

const priceRange = document.getElementById('priceRange');
if (priceRange) {
    priceRange.addEventListener('input', function () {
        const priceValue = document.getElementById('priceValue');
        if (priceValue) priceValue.textContent = this.value;
        filterTable();
    });
}

const changeFilter = document.getElementById('changeFilter');
if (changeFilter) {
    changeFilter.addEventListener('change', function () {
        filterTable();
    });
}

function filterTable() {
    const searchInput = document.getElementById('searchInput');
    const priceRange = document.getElementById('priceRange');
    const changeFilter = document.getElementById('changeFilter');
    const rows = document.querySelectorAll('#cryptoTable tbody tr');

    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const maxPrice = priceRange ? parseFloat(priceRange.value) : Infinity;
    const changeFilterValue = changeFilter ? changeFilter.value : 'all';

    rows.forEach(row => {
        const coinNameEl = row.querySelector('.coin-info strong');
        const coinName = coinNameEl ? coinNameEl.textContent.toLowerCase() : '';
        const price = parseFloat(row.dataset.price);
        const changeElement = row.querySelector('.change-column .badge');
        const change = changeElement ? changeElement.textContent : '';
        let showRow = true;

        if (!coinName.includes(searchTerm)) showRow = false;
        if (price > maxPrice) showRow = false;
        if (changeFilterValue === 'positive' && change.includes('-')) showRow = false;
        if (changeFilterValue === 'negative' && !change.includes('-')) showRow = false;

        row.style.display = showRow ? '' : 'none';
    });
}

function sortTable(criterion) {
    const tbody = document.querySelector('#cryptoTable tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.sort((a, b) => {
        let aValue, bValue;
        switch (criterion) {
            case 'price':
                aValue = parseFloat(a.dataset.price);
                bValue = parseFloat(b.dataset.price);
                return bValue - aValue;
            case 'change':
                aValue = parseFloat((a.querySelector('.change-column .badge')?.textContent || '').replace(/[+\-%]/g, ''));
                bValue = parseFloat((b.querySelector('.change-column .badge')?.textContent || '').replace(/[+\-%]/g, ''));
                return bValue - aValue;
            default:
                return 0;
        }
    });
    rows.forEach(row => tbody.appendChild(row));
}

// ---- The rest of your code (with similar pattern) ----

// All code blocks should have checks:
// const el = document.getElementById('someId');
// if (el) { el.doStuff() ... }
