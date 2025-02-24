document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
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

    // Envío del formulario de URL
    urlForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const url = videoUrlInput.value;
        if (url) {
            try {
                updateStep(1);
                showProcessingStatus();
                const formData = new FormData();
                formData.append("youtube_url", url);
                formData.append("generate_audiodesc", document.getElementById('audioDesc').checked);
                formData.append("generate_subtitles", document.getElementById('subtitles').checked);
                formData.append("voice_type", document.getElementById('voiceSelect').value);
                formData.append("subtitle_format", document.getElementById('subtitleFormat').value);
                formData.append("output_quality", document.getElementById('outputQuality').value);
                formData.append("target_language", document.getElementById('targetLanguage').value);
  
                const response = await fetch('/api/v1/videos/url', {
                    method: 'POST',
                    body: formData
                });
  
                if (!response.ok) throw new Error('Error al procesar la URL');
  
                const data = await response.json();
                currentVideoId = data.video_id;
                startProcessingCheck();
  
            } catch (error) {
                showError('Error al procesar la URL: ' + error.message);
            }
        }
    });

    // Manejo de la subida de archivos
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

    // Funcionalidad de drag and drop
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

    // Al hacer clic en "Procesar Video" (para videos subidos)
    processBtn.addEventListener('click', async function() {
        if (!currentVideoId) {
            showError('Por favor, sube un video primero');
            return;
        }

        try {
            updateStep(3);
            showProcessingStatus();
            
            const options = {
                generate_audiodesc: document.getElementById('audioDesc').checked,
                generate_subtitles: document.getElementById('subtitles').checked,
                voice_type: document.getElementById('voiceSelect').value,
                subtitle_format: document.getElementById('subtitleFormat').value,
                output_quality: document.getElementById('outputQuality').value,
                target_language: document.getElementById('targetLanguage').value
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

    // Botón para eliminar video (reinicia la subida)
    removeVideoBtn?.addEventListener('click', function() {
        resetUpload();
    });

    // Función para subir el archivo al endpoint /upload
    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('video', file);

        const response = await fetch('/api/v1/videos/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Error al subir el archivo');
        
        const data = await response.json();
        currentVideoId = data.video_id;
    }

    // Validación básica de archivo
    function validateFile(file) {
        const maxSize = 100 * 1024 * 1024; // 100MB
        const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
        return file.size <= maxSize && validTypes.includes(file.type);
    }

    // Muestra la previsualización del video
    function showFilePreview(file) {
        const url = URL.createObjectURL(file);
        videoPreview.src = url;
        uploadPreview.classList.remove('d-none');
    }

    // Muestra el estado de procesamiento
    function showProcessingStatus() {
        processingStatus.classList.remove('d-none');
    }

    // Muestra mensajes de error
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

    // Reinicia la subida y limpia el estado
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

    // Actualiza la interfaz del "stepper"
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

    // Chequea periódicamente el estado del procesamiento
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

    // Manejo de los resultados del procesamiento
    async function handleProcessingResults(videoId) {
        try {
            const response = await fetch(`/api/v1/videos/${videoId}/result`);
            const results = await response.json();

            const resultsSection = document.getElementById('resultsSection');
            resultsSection.classList.remove('d-none');

            // Actualiza el video de resultados (si existe processed_video_url)
            const resultVideo = document.getElementById('resultVideo');
            resultVideo.src = results.outputs.processed_video_url || '';

            // Agrega subtítulos si existen
            if (results.outputs.subtitles) {
                const track = document.createElement('track');
                track.kind = 'subtitles';
                track.label = 'Español';
                track.srclang = 'es';
                track.src = results.outputs.subtitles;
                resultVideo.appendChild(track);
            }

            // Actualiza la sección de descargas
            const downloadTab = document.getElementById('downloadTab');
            downloadTab.innerHTML = `
                <div class="list-group">
                    ${results.outputs.processed_video_url ? `
                        <a href="${results.outputs.processed_video_url}" class="list-group-item list-group-item-action" download>
                            <i class="bi bi-film"></i> Video Procesado
                        </a>
                    ` : ''}
                    
                    ${results.outputs.subtitles ? `
                        <a href="${results.outputs.subtitles}" class="list-group-item list-group-item-action" download>
                            <i class="bi bi-card-text"></i> Subtítulos
                        </a>
                    ` : ''}
                    
                    ${results.outputs.audio_description ? `
                        <a href="${results.outputs.audio_description}" class="list-group-item list-group-item-action" download>
                            <i class="bi bi-file-earmark-music"></i> Audiodescripción
                        </a>
                    ` : ''}
                </div>

                <div class="mt-3">
                    <h6>Resumen del Procesamiento:</h6>
                    <ul class="list-unstyled">
                        <li><i class="bi bi-clock"></i> Duración: ${results.duration || ''}</li>
                        <li><i class="bi bi-camera-video"></i> Escenas detectadas: ${results.scenesCount || ''}</li>
                        <li><i class="bi bi-chat-dots"></i> Líneas de diálogo: ${results.dialoguesCount || ''}</li>
                    </ul>
                </div>
            `;

        } catch (error) {
            console.error('Error al obtener resultados:', error);
            showError('Error al cargar los resultados del procesamiento');
        }
    }
});
