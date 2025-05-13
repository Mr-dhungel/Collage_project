document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');

    // Check if sidebar state is stored in localStorage
    const sidebarState = localStorage.getItem('sidebarState');
    if (sidebarState === 'collapsed') {
        sidebar.classList.add('collapsed');
    }

    // Make sure the toggle button works
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            sidebar.classList.toggle('collapsed');

            // Store sidebar state in localStorage
            if (sidebar.classList.contains('collapsed')) {
                localStorage.setItem('sidebarState', 'collapsed');
            } else {
                localStorage.setItem('sidebarState', 'expanded');
            }
        });
    }

    // Mobile sidebar toggle
    const mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
    if (mobileSidebarToggle) {
        mobileSidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            sidebar.classList.toggle('active');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        const isMobile = window.innerWidth <= 768;
        if (isMobile && sidebar.classList.contains('active')) {
            if (!sidebar.contains(event.target) && event.target !== mobileSidebarToggle) {
                sidebar.classList.remove('active');
            }
        }
    });

    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
        }
    });

    // Set active menu item based on current URL
    const currentUrl = window.location.pathname;
    const menuItems = document.querySelectorAll('#sidebar ul li a');

    menuItems.forEach(function(item) {
        const itemUrl = item.getAttribute('href');
        if (itemUrl && currentUrl.includes(itemUrl) && itemUrl !== '/') {
            item.parentElement.classList.add('active');
        } else if (itemUrl === '/' && currentUrl === '/') {
            item.parentElement.classList.add('active');
        }
    });

    // Log to console to verify script is running
    console.log('Sidebar script loaded and running');
});
