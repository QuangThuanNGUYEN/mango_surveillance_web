// static/js/ajax-crud.js - COMPLETE FILE

// CSRF Token helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toast notification system
function showToast(message, type = 'success') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.ajax-toast');
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `ajax-toast alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideIn 0.3s ease-out;
    `;
    
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

// Form validation helper
function validateForm(formData) {
    const errors = {};
    
    if (!formData.get('name') || formData.get('name').trim() === '') {
        errors.name = ['Threat name is required.'];
    }
    
    if (!formData.get('description') || formData.get('description').trim() === '') {
        errors.description = ['Description is required.'];
    }
    
    if (!formData.get('threat_type')) {
        errors.threat_type = ['Threat type is required.'];
    }
    
    return errors;
}

// Display form errors
function displayFormErrors(errors) {
    // Clear previous errors
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    
    // Display new errors
    for (const [field, messages] of Object.entries(errors)) {
        const input = document.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('is-invalid');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message invalid-feedback';
            errorDiv.textContent = messages[0];
            input.parentNode.appendChild(errorDiv);
        }
    }
}

// AJAX Threat Creation
function submitThreatForm(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Client-side validation
    const errors = validateForm(formData);
    if (Object.keys(errors).length > 0) {
        displayFormErrors(errors);
        return;
    }
    
    // Show loading state
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating...';
    
    fetch('/api/threats/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            form.reset();
            addThreatToList(data.threat);
            updateStats();
            
            // Close modal if it exists
            const modal = form.closest('.modal');
            if (modal) {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            }
        } else {
            showToast(data.message, 'error');
            if (data.errors) {
                displayFormErrors(data.errors);
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An unexpected error occurred. Please try again.', 'error');
    })
    .finally(() => {
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    });
}

// Add threat to the list dynamically
function addThreatToList(threat) {
    const threatsList = document.getElementById('threats-list');
    if (!threatsList) return;
    
    const threatCard = document.createElement('div');
    threatCard.className = 'col-md-6 col-lg-4 mb-3';
    threatCard.innerHTML = `
        <div class="card h-100 threat-card" data-threat-id="${threat.id}">
            <div class="card-body">
                <h5 class="card-title">${threat.name}</h5>
                <p class="card-text">${threat.description}</p>
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <span class="badge bg-${threat.threat_type === 'Pest' ? 'warning' : 'danger'}">${threat.threat_type}</span>
                    <span class="badge bg-${getRiskBadgeColor(threat.risk_level)}">${threat.risk_level}</span>
                </div>
                <div class="btn-group w-100" role="group">
                    <button class="btn btn-sm btn-outline-info" onclick="viewThreat('${threat.slug}')">
                        <i class="fas fa-eye"></i> View
                    </button>
                    <button class="btn btn-sm btn-outline-primary" onclick="editThreat(${threat.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteThreat(${threat.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
            <div class="card-footer text-muted">
                <small><i class="fas fa-clock"></i> ${threat.created_at}</small>
            </div>
        </div>
    `;
    
    threatsList.insertBefore(threatCard, threatsList.firstChild);
    
    // Add animation
    threatCard.style.opacity = '0';
    threatCard.style.transform = 'translateY(-20px)';
    setTimeout(() => {
        threatCard.style.transition = 'all 0.3s ease-out';
        threatCard.style.opacity = '1';
        threatCard.style.transform = 'translateY(0)';
    }, 100);
}

// Get risk level badge color
function getRiskBadgeColor(riskLevel) {
    switch(riskLevel.toLowerCase()) {
        case 'high': return 'danger';
        case 'moderate': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

// View threat function
function viewThreat(slug) {
    window.location.href = `/threat_list/${slug}/`;
}

// Edit threat function
function editThreat(threatId) {
    // This will be implemented in the next phase
    alert('Edit functionality will be implemented in the next update!');
}

// Delete threat with confirmation
function deleteThreat(threatId) {
    if (!confirm('Are you sure you want to delete this threat? This action cannot be undone.')) {
        return;
    }
    
    fetch(`/api/threats/${threatId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            removeThreatFromList(threatId);
            updateStats();
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred while deleting the threat.', 'error');
    });
}

// Remove threat from list
function removeThreatFromList(threatId) {
    const threatCard = document.querySelector(`[data-threat-id="${threatId}"]`);
    if (threatCard) {
        threatCard.style.transition = 'all 0.3s ease-out';
        threatCard.style.opacity = '0';
        threatCard.style.transform = 'scale(0.8)';
        setTimeout(() => {
            threatCard.closest('.col-md-6').remove();
        }, 300);
    }
}

// Update statistics
function updateStats() {
    fetch('/api/threats/')
    .then(response => response.json())
    .then(data => {
        const threats = data.threats;
        const totalThreats = threats.length;
        const pestCount = threats.filter(t => t.threat_type === 'pest').length;
        const diseaseCount = threats.filter(t => t.threat_type === 'disease').length;
        
        // Update stat cards
        const totalElement = document.getElementById('total-threats-count');
        const pestElement = document.getElementById('pest-count');
        const diseaseElement = document.getElementById('disease-count');
        
        if (totalElement) totalElement.textContent = totalThreats;
        if (pestElement) pestElement.textContent = pestCount;
        if (diseaseElement) diseaseElement.textContent = diseaseCount;
    })
    .catch(error => console.error('Error updating stats:', error));
}

// Real-time search
function setupRealTimeSearch() {
    const searchInput = document.getElementById('threat-search');
    if (!searchInput) return;
    
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            const query = this.value.toLowerCase();
            const threatCards = document.querySelectorAll('.threat-card');
            
            threatCards.forEach(card => {
                const title = card.querySelector('.card-title').textContent.toLowerCase();
                const description = card.querySelector('.card-text').textContent.toLowerCase();
                const container = card.closest('.col-md-6, .col-lg-4');
                
                if (title.includes(query) || description.includes(query)) {
                    container.style.display = 'block';
                } else {
                    container.style.display = 'none';
                }
            });
        }, 300);
    });
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Setup form submission
    const threatForm = document.getElementById('ajax-threat-form');
    if (threatForm) {
        threatForm.addEventListener('submit', submitThreatForm);
    }
    
    // Setup real-time search
    setupRealTimeSearch();
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .threat-card {
            transition: all 0.3s ease;
        }
        
        .threat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .spinner-border-sm {
            width: 1rem;
            height: 1rem;
        }
        
        .ajax-toast {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    `;
    document.head.appendChild(style);
});

// Export functions for global use
window.submitThreatForm = submitThreatForm;
window.deleteThreat = deleteThreat;
window.editThreat = editThreat;
window.viewThreat = viewThreat;