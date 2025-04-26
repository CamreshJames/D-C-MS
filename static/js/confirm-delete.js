// static/js/confirm-delete.js
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('delete-modal');
    const deleteForm = document.getElementById('delete-form');
    const deleteItemName = document.getElementById('delete-item-name');
    const cancelDelete = document.getElementById('cancel-delete');
    const closeModal = document.querySelector('.close-modal');
    const deleteError = document.getElementById('delete-error');
    
    // Attach event listeners to all delete buttons
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.dataset.id;
            const name = this.dataset.name;
            const type = this.dataset.type;
            
            // Set the form action based on type
            let formAction = '';
            switch(type) {
                case 'client':
                    formAction = `/clients/${id}/delete`;
                    break;
                case 'program':
                    formAction = `/programs/${id}/delete`;
                    break;
                case 'enrollment':
                    formAction = `/enrollments/${id}/delete`;
                    break;
            }
            
            deleteForm.action = formAction;
            deleteItemName.textContent = name;
            
            // Hide any previous error
            if (deleteError) {
                deleteError.classList.add('hidden');
            }
            
            // Show the modal
            modal.classList.add('active');
        });
    });
    
    // Close modal on cancel
    if (cancelDelete) {
        cancelDelete.addEventListener('click', function() {
            modal.classList.remove('active');
        });
    }
    
    // Close modal on X button click
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            modal.classList.remove('active');
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.classList.remove('active');
        }
    });
    
    // Handle delete form submission
    if (deleteForm) {
        deleteForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            
            try {
                const response = await fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }
                });
                
                if (response.redirected) {
                    window.location.href = response.url;
                } else if (!response.ok) {
                    const data = await response.json();
                    
                    if (deleteError) {
                        deleteError.textContent = data.detail;
                        deleteError.classList.remove('hidden');
                    }
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
});