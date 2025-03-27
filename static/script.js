// EVE Online Market Bot Web UI Script

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const systemInput = document.getElementById('system-input');
    const jumpsInput = document.getElementById('jumps-input');
    const hullsContainer = document.getElementById('hulls-container');
    const hullsLoading = document.getElementById('hulls-loading');
    const systemsList = document.getElementById('systems-list');
    const scanButton = document.getElementById('scan-button');
    const resultsContainer = document.getElementById('results-container');
    const resultsLoading = document.getElementById('results-loading');
    const noResults = document.getElementById('no-results');
    const resultsTable = document.getElementById('results-table');
    const resultsBody = document.getElementById('results-body');
    const systemInfo = document.getElementById('system-info');
    const jumpsInfo = document.getElementById('jumps-info');
    const shipTypeInfo = document.getElementById('ship-type-info');
    const themeToggle = document.getElementById('theme-toggle');
    const hullsLabel = document.getElementById('hulls-label');
    const shipTypeRadios = document.querySelectorAll('input[name="ship-type"]');

    // Theme Handling
    initTheme();
    themeToggle.addEventListener('change', switchTheme);

    // Load battleship hulls by default
    loadShipHulls('battleship');
    
    // Load solar systems for autocomplete
    loadSystems();

    // Event listeners
    scanButton.addEventListener('click', runScan);
    
    // Ship type selection event listeners
    shipTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            const shipType = this.value;
            hullsLabel.textContent = shipType === 'battleship' ? 'Battleship Hulls' : 'Cruiser Hulls';
            loadShipHulls(shipType);
        });
    });

    // Functions
    function initTheme() {
        // Check for saved theme preference or use default
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
        
        // Update toggle position based on current theme
        themeToggle.checked = savedTheme === 'light';
        
        // Update theme icons visibility
        updateThemeIcons(savedTheme);
    }
    
    function switchTheme(e) {
        const newTheme = e.target.checked ? 'light' : 'dark';
        
        // Update data attribute on html element
        document.documentElement.setAttribute('data-theme', newTheme);
        
        // Save preference to localStorage
        localStorage.setItem('theme', newTheme);
        
        // Update theme icons visibility
        updateThemeIcons(newTheme);
    }
    
    function updateThemeIcons(theme) {
        const moonIcon = document.querySelector('.theme-icon .fa-moon');
        const sunIcon = document.querySelector('.theme-icon .fa-sun');
        
        if (theme === 'dark') {
            moonIcon.style.opacity = '1';
            sunIcon.style.opacity = '0.5';
        } else {
            moonIcon.style.opacity = '0.5';
            sunIcon.style.opacity = '1';
        }
    }

    async function loadShipHulls(shipType = 'battleship') {
        try {
            // Clear existing hulls
            while (hullsContainer.firstChild) {
                hullsContainer.removeChild(hullsContainer.firstChild);
            }
            
            // Show loading spinner
            const loadingSpinner = document.createElement('div');
            loadingSpinner.className = 'loading-spinner';
            loadingSpinner.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading hulls...';
            hullsContainer.appendChild(loadingSpinner);
            
            // Fetch the appropriate ship type
            const endpoint = shipType === 'battleship' ? '/api/battleships' : '/api/cruisers';
            const response = await fetch(endpoint);
            const ships = await response.json();
            
            // Remove loading spinner
            hullsContainer.removeChild(loadingSpinner);
            
            // Create a container for all hulls
            const hullsGrid = document.createElement('div');
            hullsGrid.className = 'hulls-grid';
            
            // Create checkboxes for each ship hull
            ships.forEach(ship => {
                const label = document.createElement('label');
                label.className = 'hull-checkbox';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = ship.id;
                checkbox.checked = true; // Default to checked
                checkbox.dataset.name = ship.name;
                
                label.appendChild(checkbox);
                label.appendChild(document.createTextNode(ship.name));
                
                hullsGrid.appendChild(label);
            });
            
            hullsContainer.appendChild(hullsGrid);
            
            // Add "Select All" and "Deselect All" buttons
            const buttonContainer = document.createElement('div');
            buttonContainer.style.width = '100%';
            buttonContainer.style.marginTop = '10px';
            buttonContainer.style.display = 'flex';
            buttonContainer.style.gap = '10px';
            
            const selectAllButton = document.createElement('button');
            selectAllButton.textContent = 'Select All';
            selectAllButton.className = 'scan-button';
            selectAllButton.style.padding = '8px';
            selectAllButton.style.fontSize = '0.9rem';
            
            const deselectAllButton = document.createElement('button');
            deselectAllButton.textContent = 'Deselect All';
            deselectAllButton.className = 'scan-button';
            deselectAllButton.style.padding = '8px';
            deselectAllButton.style.fontSize = '0.9rem';
            
            selectAllButton.addEventListener('click', () => {
                document.querySelectorAll('.hull-checkbox input').forEach(checkbox => {
                    checkbox.checked = true;
                });
            });
            
            deselectAllButton.addEventListener('click', () => {
                document.querySelectorAll('.hull-checkbox input').forEach(checkbox => {
                    checkbox.checked = false;
                });
            });
            
            buttonContainer.appendChild(selectAllButton);
            buttonContainer.appendChild(deselectAllButton);
            
            hullsContainer.appendChild(buttonContainer);
            
        } catch (error) {
            console.error(`Error loading ${shipType} hulls:`, error);
            hullsContainer.innerHTML = `<div class="loading-spinner">Error loading ${shipType} hulls. Please refresh the page.</div>`;
        }
    }
    
    async function loadSystems() {
        try {
            const response = await fetch('/api/systems');
            const systems = await response.json();
            
            // Add options to datalist
            systems.forEach(system => {
                const option = document.createElement('option');
                option.value = system.name;
                option.dataset.id = system.id;
                systemsList.appendChild(option);
            });
            
        } catch (error) {
            console.error('Error loading systems:', error);
        }
    }
    
    async function runScan() {
        // Get selected hulls
        const selectedHulls = Array.from(document.querySelectorAll('.hull-checkbox input:checked'))
            .map(checkbox => checkbox.value);
        
        // Get selected ship type
        const shipType = document.querySelector('input[name="ship-type"]:checked').value;
        
        // Validate inputs
        if (!systemInput.value) {
            alert('Please enter a reference system.');
            systemInput.focus();
            return;
        }
        
        if (selectedHulls.length === 0) {
            alert(`Please select at least one ${shipType} hull.`);
            return;
        }
        
        // Show loading state
        scanButton.disabled = true;
        scanButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
        resultsContainer.style.display = 'block';
        resultsLoading.style.display = 'block';
        noResults.style.display = 'none';
        resultsBody.innerHTML = '';
        
        try {
            // Prepare request data
            const requestData = {
                system: systemInput.value,
                jumps: parseInt(jumpsInput.value),
                hulls: selectedHulls.join(','),
                shipType: shipType
            };
            
            // Send request to API
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            
            // Hide loading state
            resultsLoading.style.display = 'none';
            
            // Check for errors
            if (data.error) {
                alert(`Error: ${data.error}`);
                resultsContainer.style.display = 'none';
                return;
            }
            
            // Update results info
            systemInfo.textContent = `Reference System: ${data.reference_system}`;
            jumpsInfo.textContent = `Max Jumps: ${data.max_jumps}`;
            shipTypeInfo.textContent = `Ship Type: ${shipType.charAt(0).toUpperCase() + shipType.slice(1)}s`;
            
            // Display results
            if (data.deals && data.deals.length > 0) {
                // Populate table
                data.deals.forEach(deal => {
                    const row = document.createElement('tr');
                    
                    // Format numbers with commas
                    const formatNumber = num => num.toLocaleString('en-US', { maximumFractionDigits: 2 });
                    
                    row.innerHTML = `
                        <td>${deal.type_name}</td>
                        <td>${deal.system_name}</td>
                        <td>${deal.distance_to_reference}</td>
                        <td>${formatNumber(deal.price)} ISK</td>
                        <td>${formatNumber(deal.jita_price)} ISK</td>
                        <td>${formatNumber(deal.savings)} ISK</td>
                        <td>${deal.savings_percent.toFixed(2)}%</td>
                    `;
                    
                    // Highlight good deals (>5% savings)
                    if (deal.savings_percent > 5) {
                        row.style.color = 'var(--success-color)';
                        row.style.fontWeight = 'bold';
                    }
                    
                    resultsBody.appendChild(row);
                });
                
                // Show table
                resultsTable.style.display = 'table';
            } else {
                // Show no results message
                noResults.style.display = 'block';
                resultsTable.style.display = 'none';
            }
            
        } catch (error) {
            console.error('Error running scan:', error);
            alert('An error occurred while scanning. Please try again.');
            resultsLoading.style.display = 'none';
        } finally {
            // Reset button state
            scanButton.disabled = false;
            scanButton.innerHTML = '<i class="fas fa-search"></i> Scan for Deals';
        }
    }
});