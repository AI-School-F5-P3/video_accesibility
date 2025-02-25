console.log('Main.js cargado correctamente');
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, inicializando scripts...');

    // Elements
    const videoUrlInput = document.getElementById('videoUrl');
    const clearUrlBtn = document.getElementById('clearUrl');
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
    const resultsSection = document.getElementById('resultsSection');
    const noResultsMessage = document.getElementById('noResultsMessage');

    console.log('Elementos encontrados:', {
        videoUrlInput: !!videoUrlInput,
        clearUrlBtn: !!clearUrlBtn,
        fileInput: !!fileInput,
        uploadArea: !!uploadArea,
        processingStatus: !!processingStatus,
        processBtn: !!processBtn
    });

    let currentVideoId = null;
    let processingInterval = null;

    // Clear URL button
    clearUrlBtn?.addEventListener('click', function() {
        videoUrlInput.value = '';
        console.log('URL limpiada');
    });

    // File upload handling
    fileInput.addEventListener('change', async function(e) {
        console.log('Evento de cambio de archivo detectado');
        const file = e.target.files[0];
        if (file) {
            console.log('Archivo seleccionado:', file.name, file.type, file.size);
            try {
                if (!validateFile(file)) {
                    throw new Error('Archivo no válido. Solo se permiten videos de hasta 100MB.');
                }
                
                showFilePreview(file);
                updateStep(2);
            } catch (error) {
                showError('Error al seleccionar el archivo: ' + error.message);
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
        console.log('Archivo arrastrado detectado');
        const file = e.dataTransfer.files[0];
        
        if (file && file.type.startsWith('video/')) {
            console.log('Archivo de video arrastrado:', file.name);
            try {
                if (!validateFile(file)) {
                    throw new Error('Archivo no válido. Solo se permiten videos de hasta 100MB.');
                }
                
                fileInput.files = e.dataTransfer.files;
                showFilePreview(file);
                updateStep(2);
            } catch (error) {
                showError('Error al procesar el archivo: ' + error.message);
            }
        }
    });

    // Process button click
    processBtn.addEventListener('click', async function() {
        console.log('Botón procesar clickeado');
        try {
            console.log('Estado actual - URL:', videoUrlInput?.value);
            console.log('Estado actual - Archivo:', fileInput?.files[0]?.name || 'No hay archivo');
            
            updateStep(3);
            showProcessingStatus();
            
            // Preparar el formulario
            const formData = new FormData();
            
            // Añadir video o URL
            if (fileInput.files.length > 0) {
                console.log('Añadiendo archivo al formulario:', fileInput.files[0].name);
                formData.append('video', fileInput.files[0]);
            } else if (videoUrlInput.value) {
                console.log('Añadiendo URL al formulario:', videoUrlInput.value);
                formData.append('youtube_url', videoUrlInput.value);
            } else {
                throw new Error('Por favor, proporciona un archivo de video o una URL de YouTube');
            }
            
            // Añadir opciones
            const audioDesc = document.getElementById('audioDesc');
            const subtitles = document.getElementById('subtitles');
            console.log('Opciones seleccionadas:', {
                audiodesc: audioDesc?.checked,
                subtitles: subtitles?.checked
            });
            
            formData.append('generate_audiodesc', audioDesc?.checked || false);
            formData.append('generate_subtitles', subtitles?.checked || false);
            formData.append('subtitle_format', 'srt'); // Valor por defecto
            formData.append('target_language', 'es'); // Valor por defecto

            // Enviar a la API correcta
            console.log('Enviando petición a /api/v1/videos/process');
            const response = await fetch('/api/v1/videos/process', {
                method: 'POST',
                body: formData
            });

            console.log('Respuesta recibida:', response.status);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al iniciar el procesamiento');
            }
            
            const data = await response.json();
            console.log('Datos recibidos:', data);
            currentVideoId = data.video_id;
            startProcessingCheck();
            
        } catch (error) {
            console.error('Error processing:', error);
            showError('Error al procesar el video: ' + error.message);
        }
    });

    // Remove video button
    removeVideoBtn?.addEventListener('click', function() {
        console.log('Botón eliminar video clickeado');
        resetUpload();
    });

    // Helper functions
    function validateFile(file) {
        const maxSize = 100 * 1024 * 1024; // 100MB
        const validTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm', 'video/x-matroska'];
        const isValid = file.size <= maxSize && (validTypes.includes(file.type) || file.type.startsWith('video/'));
        console.log('Validación de archivo:', isValid, file.type, file.size);
        return isValid;
    }

    function showFilePreview(file) {
        console.log('Mostrando vista previa del archivo');
        const url = URL.createObjectURL(file);
        videoPreview.src = url;
        uploadPreview.classList.remove('d-none');
    }

    function showProcessingStatus() {
        console.log('Mostrando estado de procesamiento');
        processingStatus.classList.remove('d-none');
    }

    function showError(message) {
        console.error('Error:', message);
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
        console.log('Resetando upload');
        fileInput.value = '';
        videoPreview.src = '';
        uploadPreview.classList.add('d-none');
        processingStatus.classList.add('d-none');
        if (resultsSection) {
            resultsSection.classList.add('d-none');
        }
        currentVideoId = null;
        if (processingInterval) {
            clearInterval(processingInterval);
        }
        updateStep(1);
    }

    function updateStep(step) {
        console.log('Actualizando paso a:', step);
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
        console.log('Iniciando comprobación de procesamiento para ID:', currentVideoId);
        let progress = 0;
        processingInterval = setInterval(async () => {
            try {
                console.log('Verificando estado del procesamiento...');
                const response = await fetch(`/api/v1/videos/${currentVideoId}/status`);
                if (!response.ok) {
                    throw new Error('Error al verificar el estado');
                }
                
                const status = await response.json();
                console.log('Status update:', status);
                
                // Update progress
                if (status.progress !== undefined) {
                    progress = status.progress;
                    progressBar.style.width = `${progress}%`;
                }
                
                // Update status message
                if (status.current_step) {
                    statusText.textContent = status.current_step;
                }
                
                // Calculate estimated time
                if (progress > 0) {
                    const timeRemaining = Math.round((100 - progress) / (progress / 10));
                    estimatedTime.textContent = `Tiempo estimado: ${timeRemaining} segundos`;
                }

                // Check if processing is completed
                if (status.status === 'completed') {
                    console.log('Procesamiento completado');
                    clearInterval(processingInterval);
                    updateStep(4);
                    // Actualizar mensaje a "Procesamiento completado"
                    statusText.textContent = "Procesamiento completado";
                    progressBar.style.width = "100%";
                    estimatedTime.textContent = "";
                    await handleProcessingResults(currentVideoId);
                } 
                // Check for errors
                else if (status.status === 'error') {
                    console.log('Error en procesamiento:', status.error);
                    clearInterval(processingInterval);
                    showError(status.error || 'Error en el procesamiento');
                }
            } catch (error) {
                console.error('Error checking status:', error);
                clearInterval(processingInterval);
                showError('Error al verificar el estado del procesamiento');
            }
        }, 2000);
    }

    // Results handling
    async function handleProcessingResults(videoId) {
        console.log('Obteniendo resultados para ID:', videoId);
        try {
            const response = await fetch(`/api/v1/videos/${videoId}/result`);
            if (!response.ok) {
                throw new Error('Error al obtener resultados');
            }
            
            const results = await response.json();
            console.log('Processing results:', results);
            
            // Actualizar mensaje y mostrar botón de reinicio
            if (processingStatus) {
                // Agregar botón para reiniciar análisis si no existe ya
                if (!document.getElementById('resetAnalysisBtn')) {
                    const resetButton = document.createElement('button');
                    resetButton.id = 'resetAnalysisBtn';
                    resetButton.className = 'btn btn-primary mt-3';
                    resetButton.innerHTML = '<i class="bi bi-arrow-repeat"></i> Reiniciar análisis';
                    resetButton.onclick = resetAnalysis;
                    
                    // Añadir el botón al contenedor
                    processingStatus.querySelector('.card-body').appendChild(resetButton);
                }
            }
            
            // Si hay un elemento de resultados, mostrarlo
            if (resultsSection) {
                console.log('Mostrando sección de resultados');
                resultsSection.classList.remove('d-none');
                if (noResultsMessage) {
                    noResultsMessage.classList.add('d-none');
                }
                
                // Si hay un elemento para descargas, actualizarlo
                const downloadTab = document.getElementById('downloadTab');
                if (downloadTab) {
                    console.log('Actualizando pestaña de descargas');
                    let downloadContent = '<div class="list-group">';
                    
                    if (results.outputs && results.outputs.subtitles) {
                        downloadContent += `
                            <a href="/api/v1/subtitles/${videoId}?download=true" class="list-group-item list-group-item-action">
                                <i class="bi bi-card-text"></i> Subtítulos
                                <span class="badge bg-info float-end">SRT</span>
                            </a>
                        `;
                    }
                    
                    if (results.outputs && results.outputs.audio_description) {
                        downloadContent += `
                            <a href="/api/v1/audiodesc/${videoId}?download=true" class="list-group-item list-group-item-action">
                                <i class="bi bi-file-earmark-music"></i> Audiodescripción
                                <span class="badge bg-success float-end">WAV</span>
                            </a>
                        `;
                    }
                    
                    downloadContent += `</div>
                    <div class="mt-3">
                        <h6>Procesamiento completado</h6>
                        <p>ID del video: ${videoId}</p>
                        <button class="btn btn-outline-primary" onclick="resetAnalysis()">
                            <i class="bi bi-arrow-repeat"></i> Nuevo análisis
                        </button>
                    </div>`;
                    
                    downloadTab.innerHTML = downloadContent;
                }
                
                // Si hay un elemento de video para reproducir los resultados
                const resultVideo = document.getElementById('resultVideo');
                if (resultVideo && results.outputs && results.outputs.subtitles) {
                    console.log('Actualizando video con subtítulos');
                    // Limpiar tracks existentes
                    while (resultVideo.firstChild) {
                        resultVideo.removeChild(resultVideo.firstChild);
                    }
                    
                    // Añadir subtítulos
                    const track = document.createElement('track');
                    track.kind = 'subtitles';
                    track.label = 'Español';
                    track.srclang = 'es';
                    track.src = `/api/v1/subtitles/${videoId}?download=true`;
                    resultVideo.appendChild(track);
                }
            } else {
                // Si no hay sección de resultados, mostrar un mensaje
                console.log('Mostrando mensaje de éxito');
                const successMessage = `
                    <div class="alert alert-success">
                        <h4>¡Procesamiento completado!</h4>
                        <p>El video ha sido procesado correctamente.</p>
                        <div class="mt-2">
                            <a href="/api/v1/subtitles/${videoId}?download=true" class="btn btn-primary">Descargar Subtítulos</a>
                            ${results.outputs && results.outputs.audio_description ? 
                            `<a href="/api/v1/audiodesc/${videoId}?download=true" class="btn btn-secondary ms-2">Descargar Audiodescripción</a>` 
                            : ''}
                            <button class="btn btn-outline-primary ms-2" onclick="resetAnalysis()">
                                <i class="bi bi-arrow-repeat"></i> Nuevo análisis
                            </button>
                        </div>
                    </div>
                `;
                processingStatus.innerHTML = successMessage;
            }
        } catch (error) {
            console.error('Error al obtener resultados:', error);
            showError('Error al cargar los resultados del procesamiento');
        }
    }
    
    // Función para reiniciar el análisis
    window.resetAnalysis = function() {
        console.log('Reiniciando análisis');
        
        // Restablecer formulario
        if (fileInput) fileInput.value = '';
        if (videoUrlInput) videoUrlInput.value = '';
        if (uploadPreview) uploadPreview.classList.add('d-none');
        if (videoPreview) videoPreview.src = '';
        
        // Ocultar estados anteriores
        if (processingStatus) {
            // Limpiar contenido y ocultar
            processingStatus.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h2 class="h5">Estado del Procesamiento</h2>
                        <div class="progress mb-3">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar"></div>
                        </div>
                        <p id="statusText" class="text-muted mb-1">Preparando procesamiento...</p>
                        <p id="estimatedTime" class="small text-muted">Tiempo estimado: calculando...</p>
                    </div>
                </div>
            `;
            processingStatus.classList.add('d-none');
        }
        
        // Ocultar resultados
        if (resultsSection) {
            resultsSection.classList.add('d-none');
        }
        
        // Mostrar mensaje inicial
        if (noResultsMessage) {
            noResultsMessage.classList.remove('d-none');
        }
        
        // Restablecer checkboxes
        if (document.getElementById('audioDesc')) document.getElementById('audioDesc').checked = false;
        if (document.getElementById('subtitles')) document.getElementById('subtitles').checked = false;
        
        // Actualizar stepper al paso 1
        updateStep(1);
        
        // Limpiar estado de procesamiento
        if (processingInterval) {
            clearInterval(processingInterval);
        }
        currentVideoId = null;
    };
});