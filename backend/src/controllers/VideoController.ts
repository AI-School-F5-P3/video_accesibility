import { Request, Response } from 'express';
import { ServiceManager } from '../services/ServiceManager';

export class VideoController {
    private serviceManager: ServiceManager;

    constructor() {
        this.serviceManager = ServiceManager.getInstance();
    }

    async processVideo(req: Request, res: Response) {
        try {
            const { videoUrl, serviceType } = req.body;
            const result = await this.serviceManager.processVideoRequest(videoUrl, serviceType);
            res.json(result);
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            res.status(500).json({ error: errorMessage });
        }
    }

    async getStatus(req: Request, res: Response) {
        try {
            const { taskId } = req.params;
            const status = await this.serviceManager.getTaskStatus(taskId);
            res.json(status);
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            res.status(500).json({ error: errorMessage });
        }
    }
}
