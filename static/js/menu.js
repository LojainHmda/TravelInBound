/**
 * Side Menu (Die Menu) Functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const toggleMenuBtn = document.getElementById('toggleMenuBtn');
    const closeMenuBtn = document.getElementById('closeMenuBtn');
    const sideMenu = document.getElementById('sideMenu');
    const menuOverlay = document.getElementById('menuOverlay');
    
    // Toggle menu when burger icon is clicked
    if (toggleMenuBtn) {
        toggleMenuBtn.addEventListener('click', function() {
            sideMenu.classList.add('active');
            menuOverlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent scrolling while menu is open
        });
    }
    
    // Close menu when X button is clicked
    if (closeMenuBtn) {
        closeMenuBtn.addEventListener('click', closeMenu);
    }
    
    // Close menu when overlay is clicked
    if (menuOverlay) {
        menuOverlay.addEventListener('click', closeMenu);
    }
    
    // Close menu function
    function closeMenu() {
        sideMenu.classList.remove('active');
        menuOverlay.classList.remove('active');
        document.body.style.overflow = ''; // Re-enable scrolling
    }
    
    // Close menu when escape key is pressed
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sideMenu.classList.contains('active')) {
            closeMenu();
        }
    });
    
    // Close menu when a menu item is clicked (on mobile devices)
    const menuLinks = document.querySelectorAll('.side-menu-link');
    menuLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 992) { // Only on mobile/tablet view
                closeMenu();
            }
        });
    });
});