import { VideoIntelligenceServiceClient } from '@google-cloud/video-intelligence';
import { protos } from '@google-cloud/video-intelligence';

interface AnalysisResult {
    scenes: any[];
    labels: any[];
    objects: any[];
}

export class VisionService {
    private client: VideoIntelligenceServiceClient;

    constructor() {
        this.client = new VideoIntelligenceServiceClient({
            keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS
        });
    }

    async analyzeVideo(gcsUri: string): Promise<AnalysisResult> {
        try {
            console.log('Iniciando análisis de video:', gcsUri);
            
            const request = {
                inputUri: gcsUri,
                features: [
                    protos.google.cloud.videointelligence.v1.Feature.SHOT_CHANGE_DETECTION,
                    protos.google.cloud.videointelligence.v1.Feature.LABEL_DETECTION,
                    protos.google.cloud.videointelligence.v1.Feature.OBJECT_TRACKING
                ]
            };

            const [operation] = await this.client.annotateVideo(request);
            console.log('Operación iniciada, esperando resultados...');

            const [response] = await operation.promise();
            console.log('Análisis completado, procesando resultados...');

            if (!response || !response.annotationResults?.[0]) {
                throw new Error('No se obtuvieron resultados del análisis');
            }

            const annotationResults = response.annotationResults[0];

            // Extraer y validar resultados
            const processedResults = {
                scenes: this.extractScenes(annotationResults),
                labels: this.extractLabels(annotationResults),
                objects: this.extractObjects(annotationResults)
            };

            // Logging de resultados
            console.log('Resultados procesados:', {
                scenesCount: processedResults.scenes.length,
                labelsCount: processedResults.labels.length,
                objectsCount: processedResults.objects.length
            });

            return processedResults;

        } catch (error) {
            console.error('Error en el análisis de video:', error);
            throw new Error(`Error en el análisis: ${error instanceof Error ? error.message : 'Error desconocido'}`);
        }
    }

    private extractScenes(annotations: any): any[] {
        return annotations.shotChangeDetectionAnnotations || [];
    }

    private extractLabels(annotations: any): any[] {
        return annotations.labelAnnotations || [];
    }

    private extractObjects(annotations: any): any[] {
        return annotations.objectAnnotations || [];
    }

    async detectScenes(gcsUri: string): Promise<boolean> {
        try {
            const results = await this.analyzeVideo(gcsUri);
            const hasScenes = results.scenes.length > 0;
            console.log(`Detección de escenas completada. Encontradas: ${results.scenes.length}`);
            return hasScenes;
        } catch (error) {
            console.error('Error en detección de escenas:', error);
            return false;
        }
    }
}
