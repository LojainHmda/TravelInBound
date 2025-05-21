// Document upload and ticket analysis functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const documentTypeSelect = document.getElementById('document_type');
    const documentFileInput = document.getElementById('document_file');
    const ticketAnalysisHelper = document.getElementById('ticketAnalysisHelper');
    const extractedDataInput = document.getElementById('extracted_data');

    // Show helper message when document type is ticket
    if (documentTypeSelect) {
        documentTypeSelect.addEventListener('change', function() {
            if (this.value === 'TICKET') {
                ticketAnalysisHelper.style.display = 'block';
            } else {
                ticketAnalysisHelper.style.display = 'none';
            }
        });
        
        // Trigger on initial load
        if (documentTypeSelect.value === 'TICKET') {
            ticketAnalysisHelper.style.display = 'block';
        }
    }

    // Handle file upload and ticket analysis
    if (documentFileInput) {
        documentFileInput.addEventListener('change', function(e) {
            // Only process if document type is 'TICKET'
            if (!documentTypeSelect || documentTypeSelect.value !== 'TICKET') {
                return;
            }
            
            const file = e.target.files[0];
            if (!file) return;
            
            // Check if file is an image
            if (!file.type.match('image.*')) {
                console.log('File is not an image, skipping analysis');
                return;
            }
            
            // Show the analysis modal
            const ticketAnalysisModal = new bootstrap.Modal(document.getElementById('ticketAnalysisModal'));
            ticketAnalysisModal.show();
            
            // Show loader, hide results and error
            document.getElementById('ticketAnalysisLoader').style.display = 'block';
            document.getElementById('ticketAnalysisResults').style.display = 'none';
            document.getElementById('ticketAnalysisError').style.display = 'none';
            document.getElementById('useExtractedDataBtn').style.display = 'none';
            
            // Create form data for upload
            const formData = new FormData();
            formData.append('file', file);
            
            // Send to server for analysis
            fetch('/booking/api/analyze_ticket', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loader
                document.getElementById('ticketAnalysisLoader').style.display = 'none';
                
                if (data.error) {
                    // Show error
                    document.getElementById('ticketAnalysisError').style.display = 'block';
                    document.getElementById('error_message').textContent = data.error;
                    return;
                }
                
                // Show results
                document.getElementById('ticketAnalysisResults').style.display = 'block';
                document.getElementById('useExtractedDataBtn').style.display = 'block';
                
                const results = data.results;
                
                // Populate the results table
                document.getElementById('result_flight_number').textContent = results.flight_number || 'Not found';
                document.getElementById('result_airline').textContent = results.airline || 'Not found';
                document.getElementById('result_departure').textContent = 
                    `${results.departure_airport || 'Unknown'} ${results.departure_code ? '(' + results.departure_code + ')' : ''}`;
                document.getElementById('result_arrival').textContent = 
                    `${results.arrival_airport || 'Unknown'} ${results.arrival_code ? '(' + results.arrival_code + ')' : ''}`;
                document.getElementById('result_datetime').textContent = 
                    `${results.departure_date || 'Unknown'} ${results.departure_time || ''}`;
                document.getElementById('result_pnr').textContent = results.booking_reference || 'Not found';
                
                // Handle arrays
                document.getElementById('result_ticket_numbers').textContent = 
                    results.ticket_numbers && results.ticket_numbers.length ? results.ticket_numbers.join(', ') : 'Not found';
                document.getElementById('result_passenger_names').textContent = 
                    results.passenger_names && results.passenger_names.length ? results.passenger_names.join(', ') : 'Not found';
                
                // Store the extracted data
                extractedDataInput.value = JSON.stringify(results);
                
                // Set up button to use data
                document.getElementById('useExtractedDataBtn').addEventListener('click', function() {
                    // If we have a ticket number, use it
                    if (results.ticket_numbers && results.ticket_numbers.length) {
                        document.getElementById('document_number').value = results.ticket_numbers[0];
                    }
                    
                    // Add flight info to notes
                    const notesElement = document.getElementById('document_notes');
                    let notesText = notesElement.value || '';
                    
                    if (notesText) notesText += '\n\n';
                    
                    notesText += `Flight: ${results.flight_number || 'Unknown'}\n`;
                    notesText += `Airline: ${results.airline || 'Unknown'}\n`;
                    notesText += `From: ${results.departure_airport || 'Unknown'} ${results.departure_code ? '(' + results.departure_code + ')' : ''}\n`;
                    notesText += `To: ${results.arrival_airport || 'Unknown'} ${results.arrival_code ? '(' + results.arrival_code + ')' : ''}\n`;
                    notesText += `Date: ${results.departure_date || 'Unknown'}\n`;
                    notesText += `Time: ${results.departure_time || 'Unknown'}\n`;
                    
                    if (results.booking_reference) {
                        notesText += `Booking Reference: ${results.booking_reference}\n`;
                    }
                    
                    notesElement.value = notesText;
                    
                    // Close the modal
                    ticketAnalysisModal.hide();
                });
            })
            .catch(error => {
                console.error('Error during ticket analysis:', error);
                document.getElementById('ticketAnalysisLoader').style.display = 'none';
                document.getElementById('ticketAnalysisError').style.display = 'block';
                document.getElementById('error_message').textContent = 'An error occurred during analysis. Please try again or enter details manually.';
            });
        });
    }
});