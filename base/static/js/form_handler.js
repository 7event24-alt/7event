/**
 * Form Handler - Prevent double form submissions globally
 * Covers traditional POST forms and provides support for AJAX forms
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle traditional form submissions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        
        // Only handle POST forms
        if (form.tagName !== 'FORM') return;
        const method = form.getAttribute('method');
        if (!method || method.toLowerCase() !== 'post') return;
        
        // Skip forms with data-no-block attribute
        if (form.dataset.noBlock) return;
        
        // Skip if event was already prevented (custom handlers, validation)
        if (e.defaultPrevented) return;
        
        // Skip forms with custom onsubmit handlers (like register)
        if (form.getAttribute('onsubmit')) return;
        
        // Prevent double submit
        if (form.dataset.submitting === 'true') {
            e.preventDefault();
            return;
        }
        
        // Set submitting flag
        form.dataset.submitting = 'true';
        
        // Disable submit buttons
        const submitButtons = form.querySelectorAll('button[type="submit"]:not([data-no-block]), input[type="submit"]:not([data-no-block])');
        submitButtons.forEach(btn => {
            btn.disabled = true;
            if (!btn.dataset.originalHTML) {
                btn.dataset.originalHTML = btn.innerHTML;
            }
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
        });
        
        // Re-enable after 2 seconds if form hasn't submitted (validation error)
        setTimeout(() => {
            if (form.dataset.submitting === 'true') {
                resetFormState(form);
            }
        }, 2000);
    });
    
    // Handle HTML5 validation failures
    document.addEventListener('invalid', function(e) {
        const form = e.target.closest('form');
        if (form) {
            setTimeout(() => resetFormState(form), 100);
        }
    }, true); // Use capture to catch before submit
    
    // Debounce: prevent double-click within 2 seconds
    let lastSubmitTime = 0;
    document.addEventListener('submit', function(e) {
        const now = Date.now();
        if (now - lastSubmitTime < 2000) {
            e.preventDefault();
            return false;
        }
        lastSubmitTime = now;
    }, true);
});

/**
 * Reset form state - re-enable buttons
 */
function resetFormState(form) {
    form.dataset.submitting = 'false';
    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitButtons.forEach(btn => {
        if (btn.dataset.originalHTML) {
            btn.innerHTML = btn.dataset.originalHTML;
            btn.disabled = false;
        }
    });
}

/**
 * Handle AJAX form buttons (for forms using fetch())
 * Add data-ajax-form="true" to buttons that submit via AJAX
 */
document.addEventListener('click', function(e) {
    const btn = e.target.closest('button[type="submit"][data-ajax-form]');
    if (!btn) return;
    
    // Prevent double-click
    if (btn.disabled) {
        e.preventDefault();
        return;
    }
    
    btn.disabled = true;
    if (!btn.dataset.originalHTML) {
        btn.dataset.originalHTML = btn.innerHTML;
    }
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';
    
    // Re-enable after 2 seconds if request doesn't complete
    setTimeout(() => {
        if (btn.disabled) {
            btn.disabled = false;
            btn.innerHTML = btn.dataset.originalHTML || 'Salvar';
        }
    }, 2000);
});

/**
 * Helper function to reset AJAX button state
 * Call this in your fetch().then() and fetch().catch()
 * Usage: resetAjaxButton(buttonElement)
 */
function resetAjaxButton(btn) {
    if (btn && btn.dataset.originalHTML) {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalHTML;
    }
}

// Make helper available globally
window.resetAjaxButton = resetAjaxButton;
window.resetFormState = resetFormState;
