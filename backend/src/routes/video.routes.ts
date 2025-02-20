import { Router } from 'express';
import { VideoController } from '../controllers/VideoController';

const router = Router();
const videoController = new VideoController();

router.post('/process', videoController.processVideo.bind(videoController));
router.get('/status/:taskId', videoController.getStatus.bind(videoController));

export default router;