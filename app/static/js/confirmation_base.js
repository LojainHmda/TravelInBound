// Base confirmation functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Confirmation base script loaded');
    
    // Store original required attributes
    const originalRequiredFields = new Map();
    
    // Find all required fields and store their original state
    const requiredFields = document.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        originalRequiredFields.set(field, true);
    });
    
    // Handle Save Request button - disable HTML validation
    const saveRequestBtn = document.querySelector('button[name="action"][value="save_request"]');
    if (saveRequestBtn) {
        saveRequestBtn.addEventListener('click', function(e) {
            console.log('Save Request button clicked - disabling HTML validation');
            // Remove required attributes to bypass HTML validation
            const form = this.closest('form');
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                field.removeAttribute('required');
                field.classList.remove('is-invalid');
            });
        });
    }
    
    // Handle Confirm button - ensure HTML validation is enabled
    const confirmBtns = document.querySelectorAll('button[name="action"][value="confirm"]');
    confirmBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            console.log('Confirm button clicked - enabling HTML validation');
            // Restore required attributes for full validation
            const form = this.closest('form');
            originalRequiredFields.forEach((isRequired, field) => {
                if (isRequired) {
                    field.setAttribute('required', 'required');
                }
            });
        });
    });
    
    // Handle Next button - ensure HTML validation is enabled
    const nextBtn = document.querySelector('button[name="action"][value="next"]');
    if (nextBtn) {
        nextBtn.addEventListener('click', function(e) {
            console.log('Next button clicked - enabling HTML validation');
            // Restore required attributes for full validation
            const form = this.closest('form');
            originalRequiredFields.forEach((isRequired, field) => {
                if (isRequired) {
                    field.setAttribute('required', 'required');
                }
            });
        });
    }
    
    // Common form validation (now only applies when required attributes are present)
    const confirmationForm = document.querySelector('form');
    if (confirmationForm) {
        confirmationForm.addEventListener('submit', function(e) {
            const currentRequiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            currentRequiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    }
    
    // Initialize any date pickers
    const datePickers = document.querySelectorAll('input[type="date"]');
    datePickers.forEach(picker => {
        if (!picker.value) {
            const today = new Date().toISOString().split('T')[0];
            picker.value = today;
        }
    });
    
    // Common functionality for notes character count
    const notesTextarea = document.querySelector('textarea[name="notes"]');
    if (notesTextarea) {
        const maxLength = 500;
        const charCountSpan = document.createElement('span');
        charCountSpan.className = 'text-muted small';
        charCountSpan.textContent = `0/${maxLength} characters`;
        notesTextarea.parentNode.appendChild(charCountSpan);
        
        notesTextarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            charCountSpan.textContent = `${currentLength}/${maxLength} characters`;
            
            if (currentLength > maxLength) {
                charCountSpan.classList.add('text-danger');
                this.value = this.value.substring(0, maxLength);
                charCountSpan.textContent = `${maxLength}/${maxLength} characters`;
            } else {
                charCountSpan.classList.remove('text-danger');
            }
        });
    }
});