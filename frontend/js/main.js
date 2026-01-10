const API_BASE_URL = 'http://localhost:8000/api/v1';

document.addEventListener('DOMContentLoaded', () => {
    // Determine current page based on elements present
    if (document.querySelector('.card-grid')) {
        initSelectionPage();
    } else if (document.querySelector('.drop-zone')) {
        initUploadPage();
    } else if (document.querySelector('.result-split')) {
        initResultPage();
    }
});

// --- Page 1: Selection ---
function initSelectionPage() {
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('click', (e) => {
            e.preventDefault();
            const type = card.dataset.type; // 'passport' or 'emirates_id'
            localStorage.setItem('scanner_doc_type', type);
            window.location.href = 'upload.html';
        });
    });
}

// --- Page 2: Upload ---
function initUploadPage() {
    const docType = localStorage.getItem('scanner_doc_type');
    if (!docType) {
        window.location.href = 'index.html';
        return;
    }

    // Update UI based on type
    const title = document.getElementById('upload-title');
    if (title) {
        title.textContent = docType === 'passport' ? 'Upload Passport' : 'Upload Emirates ID';
    }

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn'); // Trigger file input

    // Click to upload (Button)
    uploadBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation(); // Prevent bubbling to dropZone
        fileInput.click();
    });

    // Click to upload (Anywhere in drop zone)
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File Input Change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0], docType);
        }
    });

    // Drag & Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0], docType);
        }
    });
}

async function handleFile(file, docType) {
    if (!file.type.match('image.*')) {
        alert('Please upload an image file (JPG, PNG).');
        return;
    }

    // Show Loader
    const loader = document.getElementById('loader');
    loader.style.display = 'flex';

    // Prepare Preview (Save to localStorage for Result Page)
    // Note: Large images might exceed quota. We'll try, catch error, and proceed.
    const reader = new FileReader();
    reader.onload = async (e) => {
        try {
            localStorage.setItem('scanner_preview_image', e.target.result);
        } catch (err) {
            console.warn('Image too large for local storage, preview might not show on next page.');
            localStorage.removeItem('scanner_preview_image');
        }

        // Upload to Backend
        await uploadToBackend(file, docType);
    };
    reader.readAsDataURL(file);
}

async function uploadToBackend(file, docType) {
    const formData = new FormData();
    formData.append('file', file);

    // Endpoint: /passport/scan or /id/scan
    // docType from selection: 'passport' or 'emirates_id'
    const endpoint = docType === 'passport' ? 'passport' : 'id';

    try {
        const response = await fetch(`${API_BASE_URL}/${endpoint}/scan`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Scan failed');
        }

        // Save Results
        localStorage.setItem('scanner_results', JSON.stringify(data));
        window.location.href = 'result.html';

    } catch (error) {
        alert(`Error: ${error.message}`);
        document.getElementById('loader').style.display = 'none';
    }
}

// --- Page 3: Result ---
function initResultPage() {
    const results = JSON.parse(localStorage.getItem('scanner_results'));
    const imageSrc = localStorage.getItem('scanner_preview_image');
    
    if (!results) {
        window.location.href = 'index.html';
        return;
    }

    // Show Image
    if (imageSrc) {
        document.getElementById('result-image').src = imageSrc;
    } else {
        document.getElementById('result-image').parentElement.style.display = 'none';
    }

    // Show Fields
    const container = document.getElementById('fields-container');
    container.innerHTML = '';

    // Metadata (Processing Time)
    const timeDiv = document.createElement('div');
    timeDiv.style.marginBottom = '1rem';
    timeDiv.style.color = '#0070f3';
    timeDiv.innerHTML = `<small>⚡ Processed in ${results.processing_time_ms.toFixed(0)}ms</small>`;
    container.appendChild(timeDiv);

    // Fields
    for (const [key, data] of Object.entries(results.fields)) {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'field-item';
        
        const label = key.replace(/_/g, ' ').toUpperCase();
        const value = data.value || 'Not detected';
        const confidence = (data.confidence * 100).toFixed(1);

        fieldDiv.innerHTML = `
            <div class="field-label">${label}</div>
            <div class="field-value">
                ${value}
                <span class="confidence-badge">${confidence}%</span>
            </div>
        `;
        container.appendChild(fieldDiv);
    }
    
    // Warnings
    if (results.warnings && results.warnings.length > 0) {
        const warnDiv = document.createElement('div');
        warnDiv.style.marginTop = '1rem';
        warnDiv.style.color = '#f5a623';
        warnDiv.innerHTML = '<strong>⚠️ Warnings:</strong><br>' + results.warnings.join('<br>');
        container.appendChild(warnDiv);
    }
}
