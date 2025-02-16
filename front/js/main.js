document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const urlForm = document.getElementById('urlForm');
    const videoUrlInput = document.getElementById('videoUrl');
    const fileInput = document.getElementById('videoFile');
    const uploadArea = document.querySelector('.upload-area');
    const processingStatus = document.getElementById('processingStatus');

    // URL form submission
    urlForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const url = videoUrlInput.value;
        if (url) {
            showProcessingStatus();
            // Aquí irá la lógica para enviar la URL a tu API
            console.log('Procesando URL:', url);
        }
    });

    // File upload handling
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            showProcessingStatus();
            // Aquí irá la lógica para enviar el archivo a tu API
            console.log('Archivo seleccionado:', file.name);
        }
    });

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dragging');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('dragging');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dragging');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('video/')) {
            fileInput.files = e.dataTransfer.files;
            showProcessingStatus();
            // Aquí irá la lógica para enviar el archivo a tu API
            console.log('Archivo soltado:', file.name);
        }
    });

    // Helper functions
    function showProcessingStatus() {
        processingStatus.classList.remove('d-none');
    }
});