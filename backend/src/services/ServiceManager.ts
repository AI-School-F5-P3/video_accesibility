import { Video } from '../models/Video';
import { QueueService } from './queue_service';
import { VisionService } from './vision/VisionService';
import { StorageService } from './storage/StorageService';
import { TextToSpeechClient } from '@google-cloud/text-to-speech';
import { AIStudioClient } from '../clients/AIStudioClient';

interface ProcessingResult {
  taskId: string;
  status: string;
  output?: string;
  error?: string;
}

export class ServiceManager {
    private static instance: ServiceManager;
    private queueService: QueueService;
    private visionService: VisionService;
    private storageService: StorageService;
    private textToSpeechClient: TextToSpeechClient;
    private aiStudioClient: AIStudioClient;

    private constructor() {
        this.queueService = new QueueService();
        this.visionService = new VisionService();
        this.storageService = new StorageService();
        this.textToSpeechClient = new TextToSpeechClient();
        this.aiStudioClient = new AIStudioClient();
    }

    public static getInstance(): ServiceManager {
        if (!ServiceManager.instance) {
            ServiceManager.instance = new ServiceManager();
        }
        return ServiceManager.instance;
    }

    async processVideoRequest(videoUrl: string, serviceType: 'AUDIODESCRIPTION' | 'SUBTITLES'): Promise<ProcessingResult> {
        try {
            const taskId = `${serviceType}_${Date.now()}`;
            const video = new Video(videoUrl);
            
            await this.queueService.enqueue_task(taskId, async () => {
                await video.download();
                const gcsUri = await video.uploadToGCS();

                if (serviceType === 'AUDIODESCRIPTION') {
                    return this.processAudioDescription(video, gcsUri);
                } else {
                    return this.processSubtitles(video, gcsUri);
                }
            });

            return { taskId, status: 'enqueued' };
        } catch (error) {
            return {
                taskId: '',
                status: 'error',
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    private async processAudioDescription(video: Video, gcsUri: string): Promise<ProcessingResult> {
        const hasScenes = await this.visionService.detectScenes(gcsUri);
        
        if (hasScenes) {
            return this.generateAudioDescription(gcsUri);
        } else {
            return this.generateFullVideoDescription(video);
        }
    }

    private async processSubtitles(video: Video, gcsUri: string): Promise<ProcessingResult> {
        return this.generateSubtitledVideo(video);
    }

    private async generateAudioDescription(gcsUri: string): Promise<ProcessingResult> {
        try {
            // Analizar escenas del video
            const analysisResult = await this.visionService.analyzeVideo(gcsUri);
            
            // Generar descripción según UNE 153020
            const description = await this.aiStudioClient.generateDescription(
                analysisResult.scenes,
                analysisResult.labels,
                analysisResult.objects
            );

            // Convertir descripción a audio
            const audioContent = await this.textToSpeechClient.synthesizeSpeech({
                input: { text: description },
                voice: { languageCode: 'es-ES', name: 'es-ES-Standard-A' },
                audioConfig: { audioEncoding: 'MP3' },
            });

            // Guardar audio en Storage
            const audioUri = await this.storageService.saveAudio(
                audioContent[0].audioContent as Buffer,
                `audio_description_${Date.now()}.mp3`
            );

            return {
                taskId: `audio_${Date.now()}`,
                status: 'completed',
                output: audioUri
            };
        } catch (error) {
            return {
                taskId: `audio_${Date.now()}`,
                status: 'error',
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    private async generateFullVideoDescription(video: Video): Promise<ProcessingResult> {
        try {
            // Generar video con descripción completa
            const videoDescription = await this.aiStudioClient.generateVideoDescription(
                await video.getMetadata()
            );

            // Procesar video con AI Studio
            const processedVideoUri = await this.aiStudioClient.processVideo(
                video,
                videoDescription,
                'UNE153020'
            );

            return {
                taskId: `video_${Date.now()}`,
                status: 'completed',
                output: processedVideoUri
            };
        } catch (error) {
            return {
                taskId: `video_${Date.now()}`,
                status: 'error',
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    private async generateSubtitledVideo(video: Video): Promise<ProcessingResult> {
        try {
            // Generar subtítulos según UNE 153010
            const subtitles = await this.aiStudioClient.generateSubtitles(
                video,
                'UNE153010'
            );

            // Procesar video con subtítulos
            const processedVideoUri = await this.aiStudioClient.addSubtitlesToVideo(
                video,
                subtitles
            );

            return {
                taskId: `subtitles_${Date.now()}`,
                status: 'completed',
                output: processedVideoUri
            };
        } catch (error) {
            return {
                taskId: `subtitles_${Date.now()}`,
                status: 'error',
                error: error instanceof Error ? error.message : 'Unknown error'
            };
        }
    }

    async getTaskStatus(taskId: string): Promise<ProcessingResult> {
        const status = await this.queueService.get_task_status(taskId);
        return { taskId, status };
    }

    // Método para limpiar recursos
    async cleanup(): Promise<void> {
        await this.queueService.cleanup();
        // Limpiar otros recursos si es necesario
    }
}
