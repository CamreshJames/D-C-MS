// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const themeIcon = themeToggle.querySelector('i');
    const themeText = themeToggle.querySelector('span');
    
    // Check if user has a theme preference in localStorage
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') {
        htmlElement.classList.add('dark-mode');
        themeIcon.className = 'bx bx-sun';
        themeText.textContent = 'Light Mode';
    }
    
    themeToggle.addEventListener('click', function() {
        htmlElement.classList.toggle('dark-mode');
        
        // Update localStorage with theme preference
        if (htmlElement.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            themeIcon.className = 'bx bx-sun';
            themeText.textContent = 'Light Mode';
        } else {
            localStorage.setItem('theme', 'light');
            themeIcon.className = 'bx bx-moon';
            themeText.textContent = 'Dark Mode';
        }
    });
    
    // Sidebar toggle functionality
    const toggleSidebar = document.querySelector('.toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    
    if (toggleSidebar && sidebar && content) {
        toggleSidebar.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            content.classList.toggle('expanded');
        });
    }
    
    // Mobile sidebar functionality
    function handleResponsiveSidebar() {
        if (window.innerWidth <= 576) {
            sidebar.classList.add('collapsed');
            content.classList.add('expanded');
            
            // Add mobile menu toggle
            if (!document.querySelector('.mobile-menu-toggle')) {
                const mobileToggle = document.createElement('button');
                mobileToggle.className = 'mobile-menu-toggle';
                mobileToggle.innerHTML = '<i class="bx bx-menu"></i>';
                document.querySelector('.page-title').prepend(mobileToggle);
                
                mobileToggle.addEventListener('click', function() {
                    sidebar.classList.toggle('mobile-visible');
                });
                
                // Close sidebar when clicking outside
                document.addEventListener('click', function(event) {
                    if (!sidebar.contains(event.target) && !mobileToggle.contains(event.target) && sidebar.classList.contains('mobile-visible')) {
                        sidebar.classList.remove('mobile-visible');
                    }
                });
            }
        } else {
            const mobileToggle = document.querySelector('.mobile-menu-toggle');
            if (mobileToggle) {
                mobileToggle.remove();
            }
            sidebar.classList.remove('mobile-visible');
        }
    }
    
    // Initial call and window resize event
    handleResponsiveSidebar();
    window.addEventListener('resize', handleResponsiveSidebar);
});