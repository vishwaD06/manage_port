/**
 * Smart Food Waste Reduction & Donation Management System
 * Interactive Client Scripts, Navigation & Modal Handling
 */

document.addEventListener('DOMContentLoaded', () => {
    // --------------------------------------------------------------------------
    // 1. Auto-dismiss Flash Alerts
    // --------------------------------------------------------------------------
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(40px)';
            setTimeout(() => alert.remove(), 400);
        }, 5000);
    });

    // Alert Close Button Handlers
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alert = e.target.closest('.alert');
            if (alert) {
                alert.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(40px)';
                setTimeout(() => alert.remove(), 250);
            }
        });
    });

    // --------------------------------------------------------------------------
    // 2. Desktop Dropdowns (Operations, Explore, User Profile)
    // --------------------------------------------------------------------------
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('navUserDropdown');

    // Handle standard nav dropdown clicks (Operations, Explore)
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const parentDropdown = toggle.closest('.nav-dropdown');
            const isOpen = parentDropdown.classList.contains('open');

            // Close all open dropdowns first
            closeAllDropdowns();

            if (!isOpen) {
                parentDropdown.classList.add('open');
                toggle.setAttribute('aria-expanded', 'true');
            }
        });
    });

    // Handle User profile dropdown click
    if (userMenuBtn && userDropdown) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = userDropdown.classList.contains('open');
            closeAllDropdowns();

            if (!isOpen) {
                userDropdown.classList.add('open');
                userMenuBtn.setAttribute('aria-expanded', 'true');
            }
        });
    }

    function closeAllDropdowns() {
        document.querySelectorAll('.nav-dropdown.open').forEach(el => {
            el.classList.remove('open');
            const btn = el.querySelector('.dropdown-toggle');
            if (btn) btn.setAttribute('aria-expanded', 'false');
        });
        if (userDropdown) {
            userDropdown.classList.remove('open');
            if (userMenuBtn) userMenuBtn.setAttribute('aria-expanded', 'false');
        }
    }

    // Close dropdowns on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.nav-dropdown') && !e.target.closest('.nav-user-dropdown')) {
            closeAllDropdowns();
        }
    });

    // --------------------------------------------------------------------------
    // 3. Mobile Navigation Drawer
    // --------------------------------------------------------------------------
    const mobileToggleBtn = document.getElementById('mobileToggleBtn');
    const mobileDrawer = document.getElementById('mobileDrawer');
    const mobileCloseBtn = document.getElementById('mobileCloseBtn');
    const mobileBackdrop = document.getElementById('mobileBackdrop');

    function openMobileDrawer() {
        if (mobileDrawer && mobileBackdrop) {
            mobileDrawer.classList.add('open');
            mobileBackdrop.classList.add('open');
            if (mobileToggleBtn) mobileToggleBtn.classList.add('open');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeMobileDrawer() {
        if (mobileDrawer && mobileBackdrop) {
            mobileDrawer.classList.remove('open');
            mobileBackdrop.classList.remove('open');
            if (mobileToggleBtn) mobileToggleBtn.classList.remove('open');
            document.body.style.overflow = 'auto';
        }
    }

    if (mobileToggleBtn) {
        mobileToggleBtn.addEventListener('click', () => {
            if (mobileDrawer && mobileDrawer.classList.contains('open')) {
                closeMobileDrawer();
            } else {
                openMobileDrawer();
            }
        });
    }

    if (mobileCloseBtn) {
        mobileCloseBtn.addEventListener('click', closeMobileDrawer);
    }

    if (mobileBackdrop) {
        mobileBackdrop.addEventListener('click', closeMobileDrawer);
    }

    // Close mobile drawer when clicking any link inside it
    if (mobileDrawer) {
        mobileDrawer.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMobileDrawer);
        });
    }

    // Keyboard navigation (Escape key closes modals, drawers, and dropdowns)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeAllDropdowns();
            closeMobileDrawer();
            document.querySelectorAll('.modal.active').forEach(modal => {
                modal.classList.remove('active');
                document.body.style.overflow = 'auto';
            });
        }
    });

    // --------------------------------------------------------------------------
    // 4. Floating Back to Top Button
    // --------------------------------------------------------------------------
    const backToTopBtn = document.getElementById('backToTopBtn');
    if (backToTopBtn) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 280) {
                backToTopBtn.classList.add('visible');
            } else {
                backToTopBtn.classList.remove('visible');
            }
        });

        backToTopBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // --------------------------------------------------------------------------
    // 5. Modal Opening and Closing Functions (Global)
    // --------------------------------------------------------------------------
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    };

    // Close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        });
    });

    // --------------------------------------------------------------------------
    // 6. Quick-Fill Demo Credentials on Login Page
    // --------------------------------------------------------------------------
    window.fillCredentials = function(role) {
        const emailInput = document.getElementById('login-email');
        const passwordInput = document.getElementById('login-password');
        if (!emailInput || !passwordInput) return;

        switch (role) {
            case 'admin':
                emailInput.value = 'admin@foodwaste.org';
                passwordInput.value = 'admin123';
                break;
            case 'donor':
                emailInput.value = 'donor.greenleaf@gmail.com';
                passwordInput.value = 'donor123';
                break;
            case 'ngo':
                emailInput.value = 'ngo.hope@charity.org';
                passwordInput.value = 'ngo123';
                break;
            case 'recycler':
                emailInput.value = 'recycler.ecobio@recycle.org';
                passwordInput.value = 'recycler123';
                break;
        }

        // Highlight inputs briefly with gentle mint glow
        [emailInput, passwordInput].forEach(input => {
            input.style.transition = 'background-color 0.3s ease, border-color 0.3s ease';
            input.style.backgroundColor = '#D8F3DC';
            input.style.borderColor = '#52B788';
            setTimeout(() => {
                input.style.backgroundColor = '';
                input.style.borderColor = '';
            }, 600);
        });
    };

    // --------------------------------------------------------------------------
    // 7. Dynamic Registration NGO Fields
    // --------------------------------------------------------------------------
    const userTypeSelect = document.getElementById('register-user-type');
    const ngoFieldsContainer = document.getElementById('ngo-specific-fields');
    if (userTypeSelect && ngoFieldsContainer) {
        const toggleNGOFields = () => {
            if (userTypeSelect.value === 'NGO/Receiver') {
                ngoFieldsContainer.style.display = 'block';
                ngoFieldsContainer.querySelectorAll('input').forEach(i => i.required = true);
            } else {
                ngoFieldsContainer.style.display = 'none';
                ngoFieldsContainer.querySelectorAll('input').forEach(i => i.required = false);
            }
        };
        userTypeSelect.addEventListener('change', toggleNGOFields);
        toggleNGOFields();
    }

    // --------------------------------------------------------------------------
    // 8. Confirmation on Destructive Actions
    // --------------------------------------------------------------------------
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', (e) => {
            const message = el.getAttribute('data-confirm') || 'Are you sure you want to proceed with this action?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});