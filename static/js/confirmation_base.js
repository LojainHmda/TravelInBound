// Base confirmation functionality
document.addEventListener('DOMContentLoaded', function() {
    // Common form validation
    const confirmationForm = document.querySelector('form');
    if (confirmationForm) {
        confirmationForm.addEventListener('submit', function(e) {
            const requiredFields = this.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
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