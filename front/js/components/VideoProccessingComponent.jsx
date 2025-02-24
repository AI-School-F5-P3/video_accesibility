import React, { useState, useEffect } from 'react';

const VideoProcessingComponent = () => {
  const [file, setFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [videoId, setVideoId] = useState(null);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Form state
  const [options, setOptions] = useState({
    generate_audiodesc: false,
    generate_subtitles: false,
    voice_type: 'es-ES-F',
    subtitle_format: 'srt',
    output_quality: 'high',
    target_language: 'es'
  });

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type.startsWith('video/')) {
      setFile(selectedFile);
      setVideoUrl('');
      setError(null);
    }
  };

  // Handle URL input
  const handleUrlChange = (e) => {
    setVideoUrl(e.target.value);
    setFile(null);
    setError(null);
  };

  // Handle options changes
  const handleOptionChange = (e) => {
    const { name, value, type, checked } = e.target;
    setOptions({
      ...options,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // Process video
  const handleProcessVideo = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const formData = new FormData();
      
      if (file) {
        formData.append('video', file);
      } else if (videoUrl) {
        formData.append('youtube_url', videoUrl);
      } else {
        throw new Error('Por favor, proporciona un archivo de video o una URL de YouTube');
      }
      
      // Add all options to formData
      Object.keys(options).forEach(key => {
        formData.append(key, options[key]);
      });
      
      // Submit to the API
      const response = await fetch('/api/v1/videos/process', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error procesando el video');
      }
      
      const data = await response.json();
      setVideoId(data.video_id);
      setProcessing(true);
      setProcessingStatus({
        status: 'started',
        message: 'Procesamiento iniciado'
      });
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Check processing status
  useEffect(() => {
    let statusInterval;
    
    if (processing && videoId) {
      statusInterval = setInterval(async () => {
        try {
          const response = await fetch(`/api/v1/videos/${videoId}/status`);
          if (!response.ok) {
            clearInterval(statusInterval);
            throw new Error('Error obteniendo el estado del procesamiento');
          }
          
          const statusData = await response.json();
          setProcessingStatus(statusData);
          
          // Update progress
          if (statusData.progress) {
            setProgress(statusData.progress);
          }
          
          // Processing completed
          if (statusData.status === 'completed') {
            clearInterval(statusInterval);
            fetchResults();
          }
          
          // Processing error
          if (statusData.status === 'error') {
            clearInterval(statusInterval);
            setError(statusData.error || 'Error durante el procesamiento');
            setProcessing(false);
          }
          
        } catch (err) {
          console.error('Status check error:', err);
          setError(err.message);
          clearInterval(statusInterval);
          setProcessing(false);
        }
      }, 3000); // Check every 3 seconds
    }
    
    return () => {
      if (statusInterval) clearInterval(statusInterval);
    };
  }, [processing, videoId]);

  // Fetch results when processing is complete
  const fetchResults = async () => {
    try {
      const response = await fetch(`/api/v1/videos/${videoId}/result`);
      
      if (!response.ok) {
        throw new Error('Error obteniendo resultados');
      }
      
      const resultData = await response.json();
      setResult(resultData);
      setProcessing(false);
      
    } catch (err) {
      console.error('Results fetch error:', err);
      setError(err.message);
      setProcessing(false);
    }
  };

  // Reset everything
  const handleReset = () => {
    setFile(null);
    setVideoUrl('');
    setVideoId(null);
    setProcessing(false);
    setProgress(0);
    setProcessingStatus(null);
    setResult(null);
    setError(null);
  };

  return (
    <div className="container py-5">
      <h2 className="mb-4">Procesamiento de Video</h2>
      
      {/* Error message */}
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}
      
      {/* Video Input Section */}
      {!processing && !result && (
        <div className="card mb-4">
          <div className="card-body">
            <h3 className="h5 mb-3">Entrada de Video</h3>
            
            {/* File upload */}
            <div className="mb-3">
              <label className="form-label">Subir archivo de video</label>
              <input 
                type="file" 
                className="form-control" 
                accept="video/*"
                onChange={handleFileChange}
                disabled={loading}
              />
            </div>
            
            <div className="text-center mb-3">- O -</div>
            
            {/* URL input */}
            <div className="mb-3">
              <label className="form-label">URL de YouTube</label>
              <input 
                type="url" 
                className="form-control"
                value={videoUrl}
                onChange={handleUrlChange}
                placeholder="https://www.youtube.com/watch?v=..."
                disabled={loading}
              />
            </div>
            
            <hr />
            
            {/* Options */}
            <h3 className="h5 mb-3">Opciones de Procesamiento</h3>
            
            <div className="row">
              <div className="col-md-6">
                <div className="form-check mb-3">
                  <input 
                    type="checkbox"
                    className="form-check-input"
                    id="generate_audiodesc"
                    name="generate_audiodesc"
                    checked={options.generate_audiodesc}
                    onChange={handleOptionChange}
                    disabled={loading}
                  />
                  <label className="form-check-label" htmlFor="generate_audiodesc">
                    Generar audiodescripción
                  </label>
                </div>
                
                {options.generate_audiodesc && (
                  <div className="mb-3">
                    <label className="form-label">Voz</label>
                    <select 
                      className="form-select"
                      name="voice_type"
                      value={options.voice_type}
                      onChange={handleOptionChange}
                      disabled={loading}
                    >
                      <option value="es-ES-F">Española (Mujer)</option>
                      <option value="es-ES-M">Español (Hombre)</option>
                    </select>
                  </div>
                )}
              </div>
              
              <div className="col-md-6">
                <div className="form-check mb-3">
                  <input 
                    type="checkbox"
                    className="form-check-input"
                    id="generate_subtitles"
                    name="generate_subtitles"
                    checked={options.generate_subtitles}
                    onChange={handleOptionChange}
                    disabled={loading}
                  />
                  <label className="form-check-label" htmlFor="generate_subtitles">
                    Generar subtítulos
                  </label>
                </div>
                
                {options.generate_subtitles && (
                  <div className="mb-3">
                    <label className="form-label">Formato</label>
                    <select 
                      className="form-select"
                      name="subtitle_format"
                      value={options.subtitle_format}
                      onChange={handleOptionChange}
                      disabled={loading}
                    >
                      <option value="srt">SRT</option>
                      <option value="vtt">VTT</option>
                    </select>
                  </div>
                )}
              </div>
            </div>
            
            <div className="row mt-3">
              <div className="col-md-6">
                <div className="mb-3">
                  <label className="form-label">Calidad</label>
                  <select 
                    className="form-select"
                    name="output_quality"
                    value={options.output_quality}
                    onChange={handleOptionChange}
                    disabled={loading}
                  >
                    <option value="high">Alta</option>
                    <option value="medium">Media</option>
                    <option value="low">Baja</option>
                  </select>
                </div>
              </div>
              
              <div className="col-md-6">
                <div className="mb-3">
                  <label className="form-label">Idioma</label>
                  <select 
                    className="form-select"
                    name="target_language"
                    value={options.target_language}
                    onChange={handleOptionChange}
                    disabled={loading}
                  >
                    <option value="es">Español</option>
                    <option value="en">Inglés</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div className="text-center mt-4">
              <button 
                className="btn btn-primary btn-lg"
                onClick={handleProcessVideo}
                disabled={loading || (!file && !videoUrl)}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    <span className="ms-2">Procesando...</span>
                  </>
                ) : 'Procesar Video'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Processing Status */}
      {processing && (
        <div className="card mb-4">
          <div className="card-body">
            <h3 className="h5 mb-3">Estado del Procesamiento</h3>
            
            <div className="mb-3">
              <div className="progress" style={{ height: '25px' }}>
                <div 
                  className="progress-bar progress-bar-striped progress-bar-animated" 
                  role="progressbar" 
                  style={{ width: `${progress}%` }}
                >
                  {progress}%
                </div>
              </div>
            </div>
            
            <div className="alert alert-info">
              <strong>Estado:</strong> {processingStatus?.current_step || 'Procesando...'}
            </div>
            
            <p className="text-muted small">
              El tiempo de procesamiento depende del tamaño del video y las opciones seleccionadas.
            </p>
          </div>
        </div>
      )}
      
      {/* Results */}
      {result && (
        <div className="card mb-4">
          <div className="card-body">
            <h3 className="h5 mb-3">Resultados del Procesamiento</h3>
            
            <div className="alert alert-success">
              <i className="bi bi-check-circle-fill me-2"></i>
              Procesamiento completado con éxito
            </div>
            
            <div className="row mt-4">
              {result.outputs?.subtitles && (
                <div className="col-md-6 mb-3">
                  <div className="card h-100">
                    <div className="card-body">
                      <h4 className="h6">Subtítulos</h4>
                      <p>Los subtítulos han sido generados correctamente.</p>
                      <a 
                        href={`/api/v1/subtitles/${videoId}?download=true`} 
                        className="btn btn-sm btn-outline-primary"
                      >
                        <i className="bi bi-download me-1"></i>
                        Descargar
                      </a>
                    </div>
                  </div>
                </div>
              )}
              
              {result.outputs?.audio_description && (
                <div className="col-md-6 mb-3">
                  <div className="card h-100">
                    <div className="card-body">
                      <h4 className="h6">Audiodescripción</h4>
                      <p>La audiodescripción ha sido generada correctamente.</p>
                      <a 
                        href={`/api/v1/audiodesc/${videoId}?download=true`}
                        className="btn btn-sm btn-outline-primary"
                      >
                        <i className="bi bi-download me-1"></i>
                        Descargar
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="text-center mt-4">
              <button className="btn btn-primary" onClick={handleReset}>
                Procesar otro video
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoProcessingComponent;