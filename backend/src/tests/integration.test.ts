import { ServiceManager } from '../services/ServiceManager';
import * as dotenv from 'dotenv';
import { resolve } from 'path';

// Configurar path correcto para .env
dotenv.config({ path: resolve(__dirname, '../../.env') });

async function testVideoProcessing() {
    const serviceManager = ServiceManager.getInstance();
    
    // URL de video de prueba de YouTube (reemplazar con un video real)
    const testVideoUrl = 'https://www.youtube.com/watch?v=your_video_id';
    
    try {
        console.log('Iniciando prueba con video:', testVideoUrl);
        
        // Probar audiodescripción
        console.log('Probando audiodescripción...');
        const audioResult = await serviceManager.processVideoRequest(
            testVideoUrl,
            'AUDIODESCRIPTION'
        );
        console.log('Resultado audiodescripción:', audioResult);
        
        // Probar subtítulos
        console.log('Probando subtítulos...');
        const subtitleResult = await serviceManager.processVideoRequest(
            testVideoUrl,
            'SUBTITLES'
        );
        console.log('Resultado subtítulos:', subtitleResult);
        
    } catch (error) {
        console.error('Error en las pruebas:', error instanceof Error ? error.message : 'Error desconocido');
    }
}

// Ejecutar la prueba y manejar la promesa
testVideoProcessing()
    .then(() => console.log('Pruebas completadas'))
    .catch(error => console.error('Error en la ejecución:', error));