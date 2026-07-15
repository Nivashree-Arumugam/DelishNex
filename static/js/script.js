/**
 * ═══════════════════════════════════════════════════════════════════════════
 * DelishNex – Main JavaScript
 * Handles dynamic UI interactions, cart management, and form logic.
 * ═══════════════════════════════════════════════════════════════════════════
 */

document.addEventListener('DOMContentLoaded', function () {

    // ═══════════════════════════════════════════════════════════════════
    // FLASH MESSAGE AUTO-DISMISS
    // ═══════════════════════════════════════════════════════════════════
    const flashMessages = document.querySelectorAll('.flash-msg');
    flashMessages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(100%)';
            setTimeout(function () { msg.remove(); }, 500);
        }, 4000);
    });

    // ═══════════════════════════════════════════════════════════════════
    // OPTION CARD SELECTION (Occasion, Mood, etc.)
    // ═══════════════════════════════════════════════════════════════════
    const optionCards = document.querySelectorAll('.option-card[data-value]');
    const optionInput = document.getElementById('option-value');

    optionCards.forEach(function (card) {
        card.addEventListener('click', function () {
            // Remove 'selected' from all cards in the same group
            optionCards.forEach(function (c) { c.classList.remove('selected'); });
            // Add 'selected' to clicked card
            card.classList.add('selected');
            // Update hidden input
            if (optionInput) {
                optionInput.value = card.getAttribute('data-value');
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════
    // DATE CARD SELECTION
    // ═══════════════════════════════════════════════════════════════════
    const dateCards = document.querySelectorAll('.date-card[data-date]');
    const dateInput = document.getElementById('date-value');

    dateCards.forEach(function (card) {
        card.addEventListener('click', function () {
            dateCards.forEach(function (c) { c.classList.remove('selected'); });
            card.classList.add('selected');
            if (dateInput) {
                dateInput.value = card.getAttribute('data-date');
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════
    // TIME CARD SELECTION
    // ═══════════════════════════════════════════════════════════════════
    const timeCards = document.querySelectorAll('.time-card[data-time]');
    const timeInput = document.getElementById('time-value');

    timeCards.forEach(function (card) {
        card.addEventListener('click', function () {
            timeCards.forEach(function (c) { c.classList.remove('selected'); });
            card.classList.add('selected');
            if (timeInput) {
                timeInput.value = card.getAttribute('data-time');
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════
    // MEMBER COUNTER
    // ═══════════════════════════════════════════════════════════════════
    const memberCount = document.getElementById('member-count');
    const memberInput = document.getElementById('member-value');
    const btnDecrease = document.getElementById('btn-decrease');
    const btnIncrease = document.getElementById('btn-increase');

    if (memberCount && btnDecrease && btnIncrease) {
        btnDecrease.addEventListener('click', function () {
            var val = parseInt(memberCount.textContent);
            if (val > 1) {
                val--;
                memberCount.textContent = val;
                if (memberInput) memberInput.value = val;
            }
        });

        btnIncrease.addEventListener('click', function () {
            var val = parseInt(memberCount.textContent);
            if (val < 20) {
                val++;
                memberCount.textContent = val;
                if (memberInput) memberInput.value = val;
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════
    // TABLE SELECTION (Restaurant Layout)
    // ═══════════════════════════════════════════════════════════════════
    const tableItems = document.querySelectorAll('.table-item:not(.booked)');
    const tableInput = document.getElementById('table-value');
    const confirmTableBtn = document.getElementById('confirm-table-btn');

    tableItems.forEach(function (item) {
        item.addEventListener('click', function () {
            tableItems.forEach(function (t) { t.classList.remove('selected'); });
            item.classList.add('selected');
            if (tableInput) {
                tableInput.value = item.getAttribute('data-table-id');
            }
            if (confirmTableBtn) {
                confirmTableBtn.disabled = false;
                confirmTableBtn.classList.remove('disabled');
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════
    // PAYMENT METHOD SELECTION
    // ═══════════════════════════════════════════════════════════════════
    const paymentOptions = document.querySelectorAll('.payment-option');
    const paymentInput = document.getElementById('payment-method');

    paymentOptions.forEach(function (option) {
        option.addEventListener('click', function () {
            paymentOptions.forEach(function (o) { o.classList.remove('selected'); });
            option.classList.add('selected');
            if (paymentInput) {
                paymentInput.value = option.getAttribute('data-method');
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════
    // DISH QUANTITY CONTROL (on Dish detail page)
    // ═══════════════════════════════════════════════════════════════════
    const qtyDisplay = document.getElementById('qty-display');
    const qtyInput = document.getElementById('qty-input');
    const btnQtyMinus = document.getElementById('btn-qty-minus');
    const btnQtyPlus = document.getElementById('btn-qty-plus');

    if (qtyDisplay && qtyInput && btnQtyMinus && btnQtyPlus) {
        btnQtyMinus.addEventListener('click', function () {
            var val = parseInt(qtyDisplay.textContent);
            if (val > 1) {
                val--;
                qtyDisplay.textContent = val;
                qtyInput.value = val;
            }
        });

        btnQtyPlus.addEventListener('click', function () {
            var val = parseInt(qtyDisplay.textContent);
            if (val < 20) {
                val++;
                qtyDisplay.textContent = val;
                qtyInput.value = val;
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════
    // FORM VALIDATION (Signup)
    // ═══════════════════════════════════════════════════════════════════
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        signupForm.addEventListener('submit', function (e) {
            var password = document.getElementById('password');
            var confirmPassword = document.getElementById('confirm_password');
            var phone = document.getElementById('phone');

            // Validate password match
            if (password && confirmPassword && password.value !== confirmPassword.value) {
                e.preventDefault();
                alert('Passwords do not match!');
                confirmPassword.focus();
                return false;
            }

            // Validate phone number (basic)
            if (phone) {
                var cleanPhone = phone.value.replace(/[\s\-\+]/g, '');
                if (cleanPhone.length < 10 || !/^\d+$/.test(cleanPhone)) {
                    e.preventDefault();
                    alert('Please enter a valid phone number (at least 10 digits).');
                    phone.focus();
                    return false;
                }
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════
    // STEP FORM VALIDATION (ensure option selected before continuing)
    // ═══════════════════════════════════════════════════════════════════
    const stepForms = document.querySelectorAll('.step-form');
    stepForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            var hiddenInput = form.querySelector('input[type="hidden"][required]');
            if (hiddenInput && !hiddenInput.value) {
                e.preventDefault();
                alert('Please make a selection before continuing.');
                return false;
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════
    // CART BADGE UPDATE (Navbar)
    // ═══════════════════════════════════════════════════════════════════
    function updateCartBadge() {
        fetch('/api/cart/count')
            .then(function (response) { return response.json(); })
            .then(function (data) {
                var badges = document.querySelectorAll('.cart-badge');
                badges.forEach(function (badge) {
                    if (data.count > 0) {
                        badge.textContent = data.count;
                        badge.style.display = 'inline';
                    } else {
                        badge.style.display = 'none';
                    }
                });
            })
            .catch(function () {
                // Silently fail — non-critical operation
            });
    }

    // Update cart badge on page load
    updateCartBadge();

    // ═══════════════════════════════════════════════════════════════════
    // SMOOTH SCROLL ANIMATIONS (Intersection Observer)
    // ═══════════════════════════════════════════════════════════════════
    var animatedElements = document.querySelectorAll('.animate-on-scroll');
    if (animatedElements.length > 0 && 'IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fadeInUp');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animatedElements.forEach(function (el) { observer.observe(el); });
    }

    // ═══════════════════════════════════════════════════════════════════
    // SEARCH BAR ENHANCEMENT
    // ═══════════════════════════════════════════════════════════════════
    var searchInput = document.getElementById('search-input');
    if (searchInput) {
        // Submit on Enter
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                var form = searchInput.closest('form');
                if (form) form.submit();
            }
        });
    }

    // ═══════════════════════════════════════════════════════════════════
    // ADMIN: Delete Confirmation
    // ═══════════════════════════════════════════════════════════════════
    var deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════
    // ADMIN: Edit Modal Population
    // ═══════════════════════════════════════════════════════════════════
    var editButtons = document.querySelectorAll('[data-bs-target="#editDishModal"]');
    editButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var modal = document.getElementById('editDishModal');
            if (!modal) return;

            modal.querySelector('#edit-dish-id').value = btn.getAttribute('data-id') || '';
            modal.querySelector('#edit-name').value = btn.getAttribute('data-name') || '';
            modal.querySelector('#edit-description').value = btn.getAttribute('data-description') || '';
            modal.querySelector('#edit-price').value = btn.getAttribute('data-price') || '';
            modal.querySelector('#edit-category').value = btn.getAttribute('data-category') || '';
            modal.querySelector('#edit-rating').value = btn.getAttribute('data-rating') || '';

            var vegCheckbox = modal.querySelector('#edit-is-vegetarian');
            if (vegCheckbox) vegCheckbox.checked = btn.getAttribute('data-veg') === '1';

            var availCheckbox = modal.querySelector('#edit-is-available');
            if (availCheckbox) availCheckbox.checked = btn.getAttribute('data-available') === '1';

            var specialCheckbox = modal.querySelector('#edit-is-special');
            if (specialCheckbox) specialCheckbox.checked = btn.getAttribute('data-special') === '1';

            // Update form action
            var editForm = modal.querySelector('#edit-dish-form');
            if (editForm) {
                editForm.action = '/admin/menu/edit/' + btn.getAttribute('data-id');
            }
        });
    });

    // ═══════════════════════════════════════════════════════════════════
    // TOOLTIP INITIALIZATION (Bootstrap)
    // ═══════════════════════════════════════════════════════════════════
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

});
