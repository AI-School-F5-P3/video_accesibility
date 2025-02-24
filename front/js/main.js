document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const urlForm = document.getElementById('urlForm');
    const videoUrlInput = document.getElementById('videoUrl');
    const fileInput = document.getElementById('videoFile');
    const uploadArea = document.querySelector('.upload-area');
    const processingStatus = document.getElementById('processingStatus');
    const uploadPreview = document.getElementById('uploadPreview');
    const videoPreview = document.getElementById('videoPreview');
    const removeVideoBtn = document.getElementById('removeVideo');
    const processBtn = document.getElementById('processBtn');
    const progressBar = document.querySelector('.progress-bar');
    const statusText = document.getElementById('statusText');
    const estimatedTime = document.getElementById('estimatedTime');

    let currentVideoId = null;
    let processingInterval = null;

    // URL form submission
    urlForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const url = videoUrlInput.value;
        if (url) {
            try {
                updateStep(1);
                showProcessingStatus();
                const response = await fetch('/api/v1/videos/url', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ url })
                });
                
                if (!response.ok) throw new Error('Error al procesar la URL');
                
                const data = await response.json();
                currentVideoId = data.videoId;
                startProcessingCheck();
                
            } catch (error) {
                showError('Error al procesar la URL: ' + error.message);
            }
        }
    });

    // File upload handling
    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (file) {
            try {
                if (!validateFile(file)) {
                    throw new Error('Archivo no válido. Solo se permiten videos de hasta 100MB.');
                }
                
                showFilePreview(file);
                updateStep(1);
                await uploadFile(file);
                
            } catch (error) {
                showError('Error al subir el archivo: ' + error.message);
            }
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

    uploadArea.addEventListener('drop', async function(e) {
        e.preventDefault();
        this.classList.remove('dragging');
        const file = e.dataTransfer.files[0];
        
        if (file && file.type.startsWith('video/')) {
            try {
                if (!validateFile(file)) {
                    throw new Error('Archivo no válido. Solo se permiten videos de hasta 100MB.');
                }
                
                fileInput.files = e.dataTransfer.files;
                showFilePreview(file);
                updateStep(1);
                await uploadFile(file);
                
            } catch (error) {
                showError('Error al procesar el archivo: ' + error.message);
            }
        }
    });

    // Process button click
    processBtn.addEventListener('click', async function() {
        if (!currentVideoId) {
            showError('Por favor, sube un video primero');
            return;
        }

        try {
            updateStep(3);
            showProcessingStatus();
            
            const options = {
                audioDescription: document.getElementById('audioDesc').checked,
                subtitles: document.getElementById('subtitles').checked,
                voice: document.getElementById('voiceSelect').value,
                subtitleFormat: document.getElementById('subtitleFormat').value
            };

            const response = await fetch(`/api/v1/videos/${currentVideoId}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(options)
            });

            if (!response.ok) throw new Error('Error al iniciar el procesamiento');
            
            startProcessingCheck();
            
        } catch (error) {
            showError('Error al procesar el video: ' + error.message);
        }
    });

    // Remove video button
    removeVideoBtn?.addEventListener('click', function() {
        resetUpload();
    });

    // Helper functions
    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('video', file);

        const response = await fetch('/api/v1/videos/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Error al subir el archivo');
        
        const data = await response.json();
        currentVideoId = data.videoId;
    }

    function validateFile(file) {
        const maxSize = 100 * 1024 * 1024; // 100MB
        const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
        return file.size <= maxSize && validTypes.includes(file.type);
    }

    function showFilePreview(file) {
        const url = URL.createObjectURL(file);
        videoPreview.src = url;
        uploadPreview.classList.remove('d-none');
    }

    function showProcessingStatus() {
        processingStatus.classList.remove('d-none');
    }

    function showError(message) {
        const alert = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        processingStatus.innerHTML = alert;
        processingStatus.classList.remove('d-none');
    }

    function resetUpload() {
        fileInput.value = '';
        videoPreview.src = '';
        uploadPreview.classList.add('d-none');
        processingStatus.classList.add('d-none');
        currentVideoId = null;
        if (processingInterval) {
            clearInterval(processingInterval);
        }
        updateStep(1);
    }

    function updateStep(step) {
        document.querySelectorAll('.stepper-item').forEach((item, index) => {
            if (index + 1 < step) {
                item.classList.add('completed');
                item.classList.remove('active');
            } else if (index + 1 === step) {
                item.classList.add('active');
                item.classList.remove('completed');
            } else {
                item.classList.remove('active', 'completed');
            }
        });
    }

    function startProcessingCheck() {
        let progress = 0;
        processingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/v1/videos/${currentVideoId}/status`);
                const status = await response.json();
                
                progress = status.progress || progress;
                progressBar.style.width = `${progress}%`;
                statusText.textContent = status.message || 'Procesando...';
                estimatedTime.textContent = `Tiempo estimado: ${status.estimatedTime || 'calculando...'}`;

                if (status.status === 'completed') {
                    clearInterval(processingInterval);
                    updateStep(4);
                    await handleProcessingResults(currentVideoId);
                } else if (status.status === 'error') {
                    clearInterval(processingInterval);
                    showError(status.error || 'Error en el procesamiento');
                }
            } catch (error) {
                clearInterval(processingInterval);
                showError('Error al verificar el estado del procesamiento');
            }
        }, 2000);
    }

    // Results handling
    async function handleProcessingResults(videoId) {
        try {
            const response = await fetch(`/api/v1/videos/${videoId}/results`);
            const results = await response.json();

            const resultsSection = document.getElementById('resultsSection');
            resultsSection.classList.remove('d-none');

            // Actualizar video con subtítulos y audiodescripción
            const resultVideo = document.getElementById('resultVideo');
            resultVideo.src = results.processedVideoUrl;

            // Añadir subtítulos si existen
            if (results.subtitles) {
                const track = document.createElement('track');
                track.kind = 'subtitles';
                track.label = 'Español';
                track.srclang = 'es';
                track.src = results.subtitles.url;
                resultVideo.appendChild(track);
            }

            // Actualizar pestaña de descargas
            const downloadTab = document.getElementById('downloadTab');
            downloadTab.innerHTML = `
                <div class="list-group">
                    ${results.processedVideoUrl ? `
                        <a href="${results.processedVideoUrl}" class="list-group-item list-group-item-action" download>
                            <i class="bi bi-film"></i> Video Procesado
                            <span class="badge bg-primary float-end">${results.videoFormat}</span>
                        </a>
                    ` : ''}
                    
                    ${results.subtitles ? `
                        <a href="${results.subtitles.url}" class="list-group-item list-group-item-action" download>
                            <i class="bi bi-card-text"></i> Subtítulos
                            <span class="badge bg-info float-end">${results.subtitles.format}</span>
                        </a>
                    ` : ''}
                    
                    ${results.audioDescription ? `
                        <a href="${results.audioDescription.url}" class="list-group-item list-group-item-action" download>
                            <i class="bi bi-file-earmark-music"></i> Audiodescripción
                            <span class="badge bg-success float-end">${results.audioDescription.format}</span>
                        </a>
                    ` : ''}
                </div>

                <div class="mt-3">
                    <h6>Resumen del Procesamiento:</h6>
                    <ul class="list-unstyled">
                        <li><i class="bi bi-clock"></i> Duración: ${results.duration}</li>
                        <li><i class="bi bi-camera-video"></i> Escenas detectadas: ${results.scenesCount}</li>
                        <li><i class="bi bi-chat-dots"></i> Líneas de diálogo: ${results.dialoguesCount}</li>
                    </ul>
                </div>
            `;

        } catch (error) {
            console.error('Error al obtener resultados:', error);
            showError('Error al cargar los resultados del procesamiento');
        }
    }
});