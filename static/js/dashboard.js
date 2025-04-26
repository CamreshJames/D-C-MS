// static/js/dashboard.js
document.addEventListener('DOMContentLoaded', function() {
    setInterval(function() {
        fetch('/api/dashboard-data')
            .then(response => response.json())
            .then(data => {
                document.getElementById('client-count').textContent = data.client_count;
                document.getElementById('program-count').textContent = data.program_count;
                document.getElementById('enrollment-count').textContent = data.enrollment_count;
            })
            .catch(error => console.error('Error updating dashboard:', error));
    }, 30000); // Update every 30 seconds
    const clientItems = document.querySelectorAll('.client-item');
    clientItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Only navigate if the click wasn't on the view button
            if (!e.target.closest('.view-btn')) {
                const viewBtn = this.querySelector('.view-btn');
                if (viewBtn && viewBtn.href) {
                    window.location.href = viewBtn.href;
                }
            }
        });
    });
    
    const programItems = document.querySelectorAll('.program-item');
    programItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Only navigate if the click wasn't on the view button
            if (!e.target.closest('.view-btn')) {
                const viewBtn = this.querySelector('.view-btn');
                if (viewBtn && viewBtn.href) {
                    window.location.href = viewBtn.href;
                }
            }
        });
    });
});