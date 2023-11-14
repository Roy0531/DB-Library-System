//  Check In Form
const radios = document.getElementsByName('inlineRadioOptions');
const checkInFields = document.querySelectorAll('.checkin-input');

radios.forEach(function(radio) {
    radio.addEventListener('change', function() {
        for (var i = 0; i < radios.length; i++) {
            if (radios[i].checked) {
                let selectedValue = radios[i].value;
                checkInFields.forEach(function(input) {
                    input.style.display = 'none';
                });
                document.getElementById(selectedValue).style.display = 'block';
                break;
            }
        }
    });
});

// searhc result 
const checkboxes = document.querySelectorAll('.borrow-check-input');
const selectedCards = [];
const borrowButton = document.querySelector('#borow-button')

checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function () {
        const bookCard = this.closest('.book-card');
        const isbnElement = bookCard.querySelector('#book-isbn');

        // Check if the checkbox is checked
        if (this.checked) {
            // Change background color of the parent .book-card to light blue
            bookCard.style.backgroundColor = 'lightblue';
            
            // Add the card and ISBN to the selectedCards array
            if (!selectedCards.some(card => card.card === bookCard)) {
                selectedCards.push({
                    isbn: isbnElement ? isbnElement.textContent.trim() : 'N/A'
                });
            }

            // Check if three checkboxes are checked, then disable others
            const checkedCheckboxes = document.querySelectorAll('.borrow-check-input:checked');
            if (checkedCheckboxes.length >= 3) {
                checkboxes.forEach(cb => {
                    if (!cb.checked) {
                        cb.disabled = true;
                    }
                });
            }
        } else {
            // If unchecked, remove background color
            bookCard.style.backgroundColor = '';
            // Remove the card from the selectedCards array
            const index = selectedCards.findIndex(card => card.card === bookCard);
            if (index !== -1) {
                selectedCards.splice(index, 1);
            }

            // Enable all checkboxes
            checkboxes.forEach(cb => {
                cb.disabled = false;
            });
        }

        // Log currently selected cards, titles, and ISBNs to the console
        console.log('Currently selected cards:', selectedCards);
    });
});