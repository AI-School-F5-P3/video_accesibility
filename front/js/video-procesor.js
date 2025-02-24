// Inicializa el componente React cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Busca el contenedor en la página
    const processingPanel = document.querySelector('.col-lg-7');
    
    if (processingPanel) {
      // Crear un div para el componente React
      const reactContainer = document.createElement('div');
      reactContainer.id = 'video-processor-container';
      
      // Reemplazar el contenido actual con nuestro contenedor
      processingPanel.innerHTML = '';
      processingPanel.appendChild(reactContainer);
      
      // Renderizar el componente React
      ReactDOM.render(
        <VideoProcessingComponent />,
        reactContainer
      );
    }
  });