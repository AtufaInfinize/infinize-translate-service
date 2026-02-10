# 🎤 Real-Time Audio Translation Service

A near real-time audio translation service that captures audio from a browser, transcribes it using AWS Transcribe, translates it with AWS Translate, and synthesizes speech with AWS Polly.

## ✨ Features

- **Real-time audio streaming** via WebSocket
- **Speech-to-text** transcription with AWS Transcribe Streaming
- **Language translation** with AWS Translate (10+ languages)
- **Text-to-speech** synthesis with AWS Polly
- **< 2 second end-to-end latency**
- **Live partial transcripts** for immediate feedback
- **Configurable language pairs** at runtime
- **Beautiful, responsive UI** with real-time metrics

## 🏗️ Architecture

```
Browser Microphone → WebSocket → FastAPI Server
                                      ↓
                              AWS Transcribe (Streaming)
                                      ↓
                              AWS Translate
                                      ↓
                              AWS Polly (TTS)
                                      ↓
WebSocket → Browser Playback
```

### Pipeline Flow
1. **Audio Capture**: Browser captures microphone audio (16kHz, mono, PCM)
2. **Streaming**: Audio chunks sent via WebSocket
3. **Transcription**: AWS Transcribe converts speech to text in real-time
4. **Translation**: AWS Translate translates final transcripts
5. **Synthesis**: AWS Polly converts translated text to speech
6. **Playback**: Audio streams back to browser for seamless playback

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** installed
- **AWS Account** with credentials configured
- **Modern web browser** (Chrome, Firefox, Edge)
- **Microphone** access

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

Your `.env` file should contain:

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
```

**Note**: Your AWS credentials are already configured in the `.env` file.

### 3. Verify AWS Permissions

Ensure your AWS IAM user has permissions for:
- `transcribe:StartStreamTranscription`
- `translate:TranslateText`
- `polly:SynthesizeSpeech`

### 4. Run the Server

```bash
# Run with uvicorn
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or alternatively:

```bash
# Run directly
python -m backend.main
```

### 5. Open Your Browser

Navigate to:
```
http://localhost:8000
```

### 6. Start Translating!

1. Select **Source Language** (e.g., English US)
2. Select **Target Language** (e.g., Spanish)
3. Click **Start Translation**
4. Grant microphone permissions
5. Start speaking!

## 🌍 Supported Languages

| Language | Code | Transcribe | Translate | Polly Voice |
|----------|------|------------|-----------|-------------|
| English (US) | en-US | ✅ | ✅ | Joanna |
| Spanish (Spain) | es-ES | ✅ | ✅ | Lucia |
| Spanish (US) | es-US | ✅ | ✅ | Lupe |
| French | fr-FR | ✅ | ✅ | Lea |
| German | de-DE | ✅ | ✅ | Vicki |
| Italian | it-IT | ✅ | ✅ | Bianca |
| Portuguese (Brazil) | pt-BR | ✅ | ✅ | Camila |
| Japanese | ja-JP | ✅ | ✅ | Kazuha |
| Korean | ko-KR | ✅ | ✅ | Seoyeon |
| Chinese (Mandarin) | zh-CN | ✅ | ✅ | Zhiyu |

## 📁 Project Structure

```
infinize_translate_service/
├── .env                          # AWS credentials (DO NOT COMMIT)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── README.md                     # This file
│
├── backend/                      # Backend Python code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Configuration & settings
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── websocket.py          # WebSocket endpoint
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pipeline_manager.py   # Core pipeline orchestration
│   │   ├── transcribe_service.py # AWS Transcribe integration
│   │   ├── translate_service.py  # AWS Translate wrapper
│   │   └── polly_service.py      # AWS Polly TTS
│   │
│   └── utils/
│       └── __init__.py
│
└── frontend/                     # Frontend HTML/JS/CSS
    ├── index.html                # Main UI
    ├── css/
    │   └── style.css             # Styles
    └── js/
        ├── audio-capture.js      # Microphone capture
        ├── audio-playback.js     # Audio playback queue
        ├── websocket-client.js   # WebSocket client
        └── app.js                # Main app controller
```

## 🔧 Configuration

### Audio Settings

Edit `backend/config.py` to adjust:

```python
sample_rate: int = 16000          # Audio sample rate (Hz)
audio_chunk_size: int = 4096      # Audio chunk size (bytes)
```

### Adding New Languages

Edit `backend/config.py` and add to `SUPPORTED_LANGUAGES`:

```python
"pt-PT": LanguageConfig(
    name="Portuguese (Portugal)",
    transcribe_code="pt-PT",
    translate_code="pt",
    polly_voice="Ines",
    polly_engine="neural"
)
```

## 📊 Performance Metrics

### Latency Breakdown (Target: < 2 seconds)

| Stage | Latency | Notes |
|-------|---------|-------|
| Audio buffering | 100-200ms | Client-side capture |
| Network upload | 50-100ms | WebSocket transmission |
| AWS Transcribe | 300-500ms | Streaming transcription |
| AWS Translate | 100-200ms | Text translation |
| AWS Polly | 200-400ms | Speech synthesis |
| Network download | 50-100ms | Audio streaming back |
| **Total** | **800-1500ms** | ✅ Under 2 seconds |

### Optimization Strategies

- ✅ Small audio chunks (100-200ms)
- ✅ Concurrent pipeline stages (async queues)
- ✅ Sentence-based translation
- ✅ PCM audio format (no encoding overhead)
- ✅ Client-side buffering (3 chunks)

## 🐛 Troubleshooting

### "Microphone permission denied"

**Solution**: Allow microphone access in your browser settings.

Chrome: `chrome://settings/content/microphone`

### "WebSocket connection failed"

**Solutions**:
- Ensure server is running on port 8000
- Check firewall settings
- Verify no other service is using port 8000

### "AWS credentials not found"

**Solution**: Verify `.env` file exists and contains valid credentials.

### "Translation is slow"

**Solutions**:
- Check your AWS region (use same region as server)
- Ensure stable internet connection
- Monitor AWS service health status

### "No audio playback"

**Solutions**:
- Check browser audio permissions
- Verify speakers/headphones are working
- Check browser console for errors

## 💰 AWS Costs

### Estimated Costs (per hour of active use)

- **AWS Transcribe**: $0.024/minute = ~$1.44/hour
- **AWS Translate**: ~$0.50/hour (moderate use)
- **AWS Polly**: ~$0.30/hour
- **Total**: ~$2.24/hour of active translation

### Cost Optimization Tips

- Only translate final transcripts (not partials)
- Use sentence-based chunking
- Implement silence detection
- Stop translation when not in use

## 🔒 Security Considerations

### Production Checklist

- [ ] **Restrict CORS origins** in `backend/main.py`
- [ ] **Use environment variables** for all secrets
- [ ] **Enable HTTPS/WSS** for secure connections
- [ ] **Implement rate limiting** to prevent abuse
- [ ] **Add user authentication** if needed
- [ ] **Monitor AWS costs** with CloudWatch
- [ ] **Set up CloudWatch alarms** for unusual activity
- [ ] **Never commit `.env`** to version control

## 🧪 Testing

### Manual Testing

1. Start the server
2. Open browser to `http://localhost:8000`
3. Select language pair
4. Start translation
5. Speak clearly in source language
6. Verify:
   - ✅ Partial transcripts appear in real-time
   - ✅ Final transcripts are accurate
   - ✅ Translation is correct
   - ✅ Audio playback is smooth
   - ✅ Latency < 2 seconds

### Test Different Scenarios

- ✅ Short phrases
- ✅ Long sentences
- ✅ Multiple speakers
- ✅ Background noise
- ✅ Different languages
- ✅ Network interruptions (reconnection)

## 📚 API Documentation

### WebSocket Protocol

#### Client → Server Messages

**Configuration**
```json
{
  "type": "config",
  "source_language": "en-US",
  "target_language": "es-ES"
}
```

**Audio Chunk**
```json
{
  "type": "audio",
  "audio": "base64_encoded_pcm_data"
}
```

**Stop**
```json
{
  "type": "stop"
}
```

#### Server → Client Messages

**Partial Transcript**
```json
{
  "type": "partial_transcript",
  "text": "Hello, how are..."
}
```

**Final Transcript**
```json
{
  "type": "transcript",
  "text": "Hello, how are you?",
  "is_final": true
}
```

**Translation**
```json
{
  "type": "translation",
  "original": "Hello, how are you?",
  "translated": "Hola, ¿cómo estás?",
  "latency_ms": 150
}
```

**Audio Chunk**
```json
{
  "type": "audio",
  "audio": "base64_encoded_pcm_data",
  "chunk_index": 0,
  "is_last": false
}
```

**Error**
```json
{
  "type": "error",
  "message": "Error description",
  "stage": "transcribe|translate|tts"
}
```

## 🚀 Deployment

### Local Development
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (with Gunicorn)
```bash
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add more languages
- [ ] Implement conversation history
- [ ] Add user authentication
- [ ] Support multiple concurrent sessions
- [ ] Add mobile app support
- [ ] Implement silence detection
- [ ] Add voice activity detection (VAD)
- [ ] Support different audio formats

## 📝 License

This project uses AWS services which have their own pricing and terms of service.

## 🙏 Acknowledgments

- **AWS Transcribe** - Real-time speech recognition
- **AWS Translate** - Neural machine translation
- **AWS Polly** - Natural-sounding text-to-speech
- **FastAPI** - Modern Python web framework
- **Web Audio API** - Browser audio processing

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review AWS service status
- Check browser console for errors
- Verify AWS credentials and permissions

---

Built with ❤️ for near real-time audio translation
