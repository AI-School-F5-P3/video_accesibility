console.log('Main.js cargado correctamente');
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado, inicializando scripts...');

    // Elements - usando let en lugar de const para los elementos que se reasignan
    const videoUrlInput = document.getElementById('videoUrl');
    const clearUrlBtn = document.getElementById('clearUrl');
    const fileInput = document.getElementById('videoFile');
    const uploadArea = document.querySelector('.upload-area');
    const processingStatus = document.getElementById('processingStatus');
    const uploadPreview = document.getElementById('uploadPreview');
    const videoPreview = document.getElementById('videoPreview');
    const removeVideoBtn = document.getElementById('removeVideo');
    const processBtn = document.getElementById('processBtn');
    const integratedVideoOption = document.getElementById('integratedVideo');
    let progressBar = document.querySelector('.progress-bar');
    let statusText = document.getElementById('statusText');
    let estimatedTime = document.getElementById('estimatedTime');
    const resultsSection = document.getElementById('resultsSection');
    const noResultsMessage = document.getElementById('noResultsMessage');
    const completionMessage = document.getElementById('completionMessage');

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
            
            // Ocultar mensaje de completado si estaba visible
            if (completionMessage) {
                completionMessage.classList.add('d-none');
            }
            
            updateStep(3);
            showProcessingStatus();
            
            // Forzar la animación de la barra de progreso inmediatamente
            progressBar.style.width = "5%"; // Comenzar con un pequeño avance visible
            
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
                subtitles: subtitles?.checked,
                integrated_video: integratedVideoOption?.checked
            });
            
            formData.append('generate_audiodesc', audioDesc?.checked || false);
            formData.append('generate_subtitles', subtitles?.checked || false);
            formData.append('integrated_video', integratedVideoOption?.checked || false);
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
        // Asegurarse de que no haya mensajes de error previos
        processingStatus.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h2 class="h5">Estado del Procesamiento</h2>
                    <p id="statusText" class="text-muted mb-1">Preparando procesamiento...</p>
                    
                    <!-- Mensaje de paciencia -->
                    <p class="text-info mb-3">
                        <i class="bi bi-info-circle-fill me-1"></i>
                        <small>Ten paciencia, el proceso puede durar unos minutos. Aún estamos en pruebas</small>
                    </p>
                    
                    <div class="progress mb-3">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 5%"></div>
                    </div>
                    <p id="estimatedTime" class="small text-muted">Tiempo estimado: calculando...</p>
                </div>
            </div>
        `;
        
        // Volver a obtener referencias a los elementos después de recrearlos
        statusText = document.getElementById('statusText');
        estimatedTime = document.getElementById('estimatedTime');
        progressBar = document.querySelector('.progress-bar');
    }

    function showError(message) {
        console.error('Error:', message);
        
        // Ocultar mensaje de completado si estaba visible
        if (completionMessage) {
            completionMessage.classList.add('d-none');
        }
        
        const alertHTML = `
            <div class="card">
                <div class="card-body">
                    <div class="alert alert-danger" role="alert">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        ${message}
                    </div>
                    <button class="btn btn-outline-primary" onclick="resetAnalysis()">
                        <i class="bi bi-arrow-repeat"></i> Intentar de nuevo
                    </button>
                </div>
            </div>
        `;
        processingStatus.innerHTML = alertHTML;
        processingStatus.classList.remove('d-none');
    }

    function resetUpload() {
        console.log('Resetando upload');
        fileInput.value = '';
        videoPreview.src = '';
        uploadPreview.classList.add('d-none');
        processingStatus.classList.add('d-none');
        
        // Ocultar mensaje de completado
        if (completionMessage) {
            completionMessage.classList.add('d-none');
        }
        
        if (resultsSection) {
            resultsSection.classList.add('d-none');
        }
        if (noResultsMessage) {
            noResultsMessage.classList.remove('d-none');
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
                    
                    // Reemplazar el panel de procesamiento con un mensaje de éxito
                    processingStatus.innerHTML = `
                        <div class="card">
                            <div class="card-body text-center">
                                <i class="bi bi-check-circle-fill text-success display-1 mb-3"></i>
                                <h2 class="h4">¡Procesamiento completado!</h2>
                                <p class="text-success">Tus resultados están listos :)</p>
                                <button class="btn btn-outline-primary mt-2" onclick="resetAnalysis()">
                                    <i class="bi bi-arrow-repeat"></i> Nuevo análisis
                                </button>
                            </div>
                        </div>
                    `;
                    
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
                            <a href="${results.outputs.subtitles}" class="list-group-item list-group-item-action">
                                <i class="bi bi-card-text"></i> Subtítulos
                                <span class="badge bg-info float-end">SRT</span>
                            </a>
                        `;
                    }
                    
                    if (results.outputs && results.outputs.audio_description) {
                        downloadContent += `
                            <a href="${results.outputs.audio_description}" class="list-group-item list-group-item-action">
                                <i class="bi bi-file-earmark-music"></i> Audiodescripción
                                <span class="badge bg-success float-end">MP3</span>
                            </a>
                        `;
                    }
                    
                    // Añadir opción para el video integrado
                    if (results.outputs && results.outputs.integrated_video) {
                        downloadContent += `
                            <a href="${results.outputs.integrated_video}" class="list-group-item list-group-item-action">
                                <i class="bi bi-film"></i> Video con accesibilidad integrada
                                <span class="badge bg-primary float-end">MP4</span>
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
                
                // No necesitamos actualizar la vista previa ya que ahora muestra "Próximamente"
                console.log('Vista previa desactivada temporalmente');
            } else {
                // Si no hay sección de resultados, mostrar un mensaje
                console.log('No se encontró la sección de resultados');
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
        
        // Ocultar mensaje de completado
        if (completionMessage) {
            completionMessage.classList.add('d-none');
        }
        
        // Ocultar estados anteriores
        if (processingStatus) {
            // Limpiar contenido y ocultar
            processingStatus.innerHTML = `
                <div class="card">
                    <div class="card-body">
                        <h2 class="h5">Estado del Procesamiento</h2>
                        <p id="statusText" class="text-muted mb-1">Preparando procesamiento...</p>
                        
                        <!-- Mensaje de paciencia -->
                        <p class="text-info mb-3">
                            <i class="bi bi-info-circle-fill me-1"></i>
                            <small>Ten paciencia, el proceso puede durar unos minutos. Aún estamos en pruebas</small>
                        </p>
                        
                        <div class="progress mb-3">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 role="progressbar" style="width: 0%"></div>
                        </div>
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
        if (document.getElementById('integratedVideo')) document.getElementById('integratedVideo').checked = true;
        
        // Actualizar stepper al paso 1
        updateStep(1);
        
        // Limpiar estado de procesamiento
        if (processingInterval) {
            clearInterval(processingInterval);
        }
        currentVideoId = null;
    };
});