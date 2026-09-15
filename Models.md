# Models

Select a preset, enter a model reference, or browse for a local model file.

- Hugging Face: `hf://owner/repository/filename`.
- Ultralytics Platform: `ul://owner/project/model` or a model-page URL. Set `ULTRALYTICS_API_KEY` for API downloads.
- Device: `cpu` or a GPU index such as `0`; leave blank for Ultralytics defaults.
- For classifiers trained on cropped faces, select a face model under **Crop detector**.

## Presets

| Preset | Source | Output |
| --- | --- | --- |
| rpi5/person-detection/yolov8nbest | [Ultralytics Platform](https://platform.ultralytics.com/rpi5/person-detection/yolov8nbest) | Model-provided detection labels |
| leeyunjai/yolo11-ko-face-emotion-cls | [Model source](https://huggingface.co/leeyunjai/yolo11-ko-face-emotion-cls) | Model-provided labels from `yolo11x-face-emotion.pt` |
| NguyenToanLe/Age-Gender-Detection-YOLO / age, gender | [Model sources](https://github.com/NguyenToanLe/Age-Gender-Detection-YOLO/tree/main/models) | Separate `age.pt` and `gender.pt` checkpoints; labels read from each model |
| DhanushSGowda/yolov8n-gender-classification | [Model source](https://huggingface.co/DhanushSGowda/yolov8n-gender-classification) | Whole-image class probabilities |
| AdamCodd/yolo11n-face-age | [Model source](https://huggingface.co/AdamCodd/yolo11n-face-age) | Face boxes with age-range labels |
| MnLgt/yolo-human-parse | [Model source](https://huggingface.co/MnLgt/yolo-human-parse) | Body-part and object labels from segmentation detections |
| yolo26n-cls | [Ultralytics](https://platform.ultralytics.com/ultralytics/yolo26/yolo26n-cls) | Whole-image class probabilities; Ultralytics downloads `yolo26n-cls.pt` by name |
| yolo11n-cls | [Ultralytics](https://platform.ultralytics.com/ultralytics/yolo11/yolo11n-cls) | Whole-image class probabilities; Ultralytics downloads `yolo11n-cls.pt` by name |
| yolov8n-cls | [Ultralytics](https://platform.ultralytics.com/ultralytics/yolov8/yolov8n-cls) | Whole-image class probabilities; Ultralytics downloads `yolov8n-cls.pt` by name |
| dgyawa/yolo12n-cls-imagenet1k | [Model source](https://huggingface.co/dgyawa/yolo12n-cls-imagenet1k) | Whole-image class probabilities from `yolo12n-cls.pt` |
| Anzhcs Breast size det cls v8 640 y11m | [Model source](https://huggingface.co/Anzhc/Anzhcs_YOLOs/blob/main/Anzhcs%20Breast%20size%20det%20cls%20v8%20640%20y11m.pt) | Detection boxes with model-provided labels |
| yolov8n-oiv7, yolov8l-oiv7, yolov8x-oiv7 | [Ultralytics](https://docs.ultralytics.com/datasets/detect/open-images-v7) | Open Images V7 detection labels; Ultralytics downloads weights by name |
| yolov8s-oiv7, yolov8m-oiv7 | [Model source](https://huggingface.co/shirabendor/YOLOV8-oiv7) | Open Images V7 detection labels |
| booru_yolo variants | [Model sources](https://github.com/aperveyev/booru_yolo/tree/main/models) | Detection boxes with model-provided labels |

The booru_yolo dropdown variants are `yolov11m_aa22`, `yolov11m_mm07`, `yolov11m_pp15`, `yolov8m_as02`, `yolov8m_as03`, `yolov8m_pp14`, `yolov8n_as01`, `yolov8s_aa06`, `yolov8s_aa09`, `yolov8s_aa10`, `yolov8s_aa11`, `yolov8s_pp09`, and `yolov8s_pp12`. ZIP-packaged checkpoints are extracted inside the app's model directory on first use.
