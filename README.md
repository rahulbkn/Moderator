# Image Moderation API

A production-ready image moderation API built with FastAPI and NudeNet, optimized for 512 MB RAM and CPU-only inference.

## Endpoints

### `GET /health`
Health check.

### `POST /moderate`
Moderate an image from a Cloudinary URL.

**Request:**
```json
{
  "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg"
}
```

**Response (NSFW detected):**
```json
{
  "success": true,
  "safe": false,
  "nsfw_score": 0.98,
  "detections": [
    {
      "label": "EXPOSED_BREAST_F",
      "confidence": 0.99
    }
  ]
}
```

**Response (safe):**
```json
{
  "success": true,
  "safe": true,
  "nsfw_score": 0.0,
  "detections": []
}
```

## Deployment on Render

### One-click via render.yaml
1. Push this repo to GitHub.
2. In the Render Dashboard, click **New → Blueprint**.
3. Connect your repo and Render auto-detects `render.yaml`.

### Manual
1. Create a new **Web Service** on Render.
2. Select **Python** runtime.
3. Set **Build Command**:
   ```
   pip install -r requirements.txt
   ```
4. Set **Start Command**:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
   ```
5. Choose the **Starter** plan (512 MB RAM).
6. Deploy.

## Integration with Android App

1. Upload image to Cloudinary from your Android app.
2. Send the Cloudinary URL to this API:
   ```kotlin
   // Kotlin/Retrofit example
   data class ModerateRequest(val image_url: String)
   data class Detection(val label: String, val confidence: Double)
   data class ModerateResponse(
       val success: Boolean,
       val safe: Boolean,
       val nsfw_score: Double,
       val detections: List<Detection>
   )

   interface ModerationApi {
       @POST("moderate")
       suspend fun moderate(@Body request: ModerateRequest): ModerateResponse
   }
   ```
3. Check `safe` field: if `true`, the image is safe to display.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_IMAGE_SIZE` | `1280` | Max dimension for image resizing |
| `MIN_IMAGE_SIZE` | `640` | Minimum longest edge; smaller images are upscaled before inference |
| `MODEL_INFERENCE_RESOLUTION` | `640` | NudeNet inference resolution for improved small-detail detection |
| `NSFW_THRESHOLD` | `0.45` | Score threshold used to mark an image unsafe |
| `NSFW_MULTI_DETECTION_THRESHOLD` | `0.38` | Lower threshold applied when multiple NSFW body-part detections are found |
| `LOG_LEVEL` | `INFO` | Logging level |
| `REQUEST_TIMEOUT` | `30` | HTTP request timeout in seconds |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `CLOUD_VISION_ENABLED` | `false` | Enable Google Cloud Vision SafeSearch in addition to NudeNet |
| `CLOUD_VISION_MIN_SCORE` | `0.5` | Minimum mapped SafeSearch score to include as a moderation signal |
| `GOOGLE_CLOUD_VISION_CREDENTIALS_JSON` | unset | Full Google service-account JSON key; enables Cloud Vision automatically when set |
| `GOOGLE_APPLICATION_CREDENTIALS` | unset | Alternative Google-supported path to a service-account JSON key file |

## Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Google Cloud Vision key setup

Do **not** commit your Google service-account JSON key to this repository. Add it as an environment variable in your hosting provider instead.

### Render / hosted deployment

1. Open your Render service dashboard.
2. Go to **Environment**.
3. Add `GOOGLE_CLOUD_VISION_CREDENTIALS_JSON`.
4. Paste the full service-account JSON key as the value. Use the raw JSON from Google Cloud, preferably minified onto one line.
5. Save and redeploy the service.

When `GOOGLE_CLOUD_VISION_CREDENTIALS_JSON` is set, Cloud Vision SafeSearch is enabled automatically. You may also set `CLOUD_VISION_ENABLED=true` explicitly.

### Local development

For local testing, either export the full JSON key:

```bash
export GOOGLE_CLOUD_VISION_CREDENTIALS_JSON='{"type":"service_account","project_id":"..."}'
```

Or save the JSON key outside the repo and point Google Application Default Credentials to it:

```bash
export CLOUD_VISION_ENABLED=true
export GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/outside/this/repo/service-account.json
```

The JSON key needs permission to call the Google Cloud Vision API, and the Vision API must be enabled for the key's Google Cloud project.
