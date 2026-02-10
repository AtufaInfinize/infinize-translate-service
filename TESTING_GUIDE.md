# 🧪 Testing Guide - Deepgram Transcription

## ✅ Server is Running with Enhanced Logging!

The server now has comprehensive logging to help debug transcription issues.

## 📋 What Logs to Expect

When you use the application, you should see these logs in order:

### 1. WebSocket Connection
```
INFO - WebSocket connection established from ...
INFO - Configuration received: en-US -> es-ES
```

### 2. Pipeline Starting
```
DEBUG - Using Deepgram Nova-2 model for transcription
INFO - Starting transcribe stage with DEEPGRAM
```

### 3. Deepgram Initialization
```
============================================================
🎤 DEEPGRAM TRANSCRIPTION STARTING
Language: en
============================================================
INFO - Deepgram options: {'model': 'nova-2', ...}
INFO - Creating Deepgram WebSocket connection...
```

### 4. Connection Success
```
✅ Deepgram WebSocket connection OPENED successfully
✅ Deepgram transcription STARTED for language: en
🎧 Waiting for audio chunks...
```

### 5. Audio Streaming
```
📤 Sent 50 audio chunks to Deepgram
📤 Sent 100 audio chunks to Deepgram
...
```

### 6. Transcription Results
```
📝 Partial: 'Hello this is...'
📝 Partial: 'Hello this is a test...'
✅ FINAL TRANSCRIPT: 'Hello, this is a test.' (confidence: 0.95)
```

### 7. Translation & TTS
```
INFO - Translated: 'Hello, this is a test.' -> 'Hola, esto es una prueba.'
INFO - Sent X audio chunks for text: 'Hola, esto es una prueba.'
```

## 🧪 How to Test

### Step 1: Open Browser
```
http://localhost:8000
```

### Step 2: Open Terminal to Watch Logs
In a new terminal:
```bash
tail -f server.log
```

### Step 3: Start Translation
1. Select Source: **English (US)**
2. Select Target: **Spanish**
3. Click **"Start Translation"**
4. Grant microphone permission

### Step 4: Speak and Watch Logs
Say clearly: **"Hello, this is a test"**

Watch the terminal for:
- ✅ Connection opened
- 📤 Audio chunks being sent
- ✅ Final transcript appearing

## 🐛 Troubleshooting

### Problem: No logs after "Start Translation"

**Possible causes:**
1. **Microphone not working**
   - Check browser permissions
   - Try another browser (Chrome/Firefox)

2. **WebSocket not connecting**
   - Check browser console (F12)
   - Look for WebSocket errors

3. **Audio not being captured**
   - Check microphone in system settings
   - Test microphone in another app

### Problem: "Deepgram connection opened" but no transcripts

**Possible causes:**
1. **Speaking too quietly**
   - Speak louder and clearer
   - Check microphone levels

2. **Background noise**
   - Test in quiet environment
   - Use headset microphone

3. **Audio format issue**
   - Check logs for "Received empty audio chunk"
   - May need to adjust audio settings

### Problem: Partial transcripts but no final transcripts

**Possible causes:**
1. **Speaking too fast**
   - Pause between sentences
   - Wait 1-2 seconds after speaking

2. **Utterance detection issue**
   - The model needs silence to finalize
   - Stop speaking for 1 second

## 📊 Expected Log Flow (Complete Example)

```
# 1. Connection
INFO - WebSocket connection established
INFO - Configuration received: en-US -> es-ES

# 2. Pipeline Start
============================================================
🎤 DEEPGRAM TRANSCRIPTION STARTING
Language: en
============================================================

# 3. WebSocket  Open
✅ Deepgram WebSocket connection OPENED successfully
🎧 Waiting for audio chunks...

# 4. Audio Streaming
📤 Sent 50 audio chunks to Deepgram
📤 Sent 100 audio chunks to Deepgram

# 5. Transcription
📝 Partial: 'Hello'
📝 Partial: 'Hello this'
📝 Partial: 'Hello this is'
📝 Partial: 'Hello this is a test'
✅ FINAL TRANSCRIPT: 'Hello, this is a test.' (confidence: 0.95)

# 6. Translation
INFO - Translated: 'Hello, this is a test.' -> 'Hola, esto es una prueba.'

# 7. Audio Output
INFO - Sent 5 audio chunks for text: 'Hola, esto es una prueba.'
```

## 🎯 Quick Test Commands

### Test 1: Check Server is Running
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

### Test 2: Check Configuration
```bash
curl http://localhost:8000/api/config
# Should show: sample_rate, aws_region, etc.
```

### Test 3: Watch Live Logs
```bash
tail -f server.log | grep -E "🎤|✅|📝|📤"
# Shows only important transcription logs
```

## 💡 Tips for Best Results

1. **Speak Clearly**
   - Normal pace, not too fast
   - Enunciate words clearly

2. **Good Microphone**
   - Headset mic is best
   - Position 6-12 inches from mouth

3. **Quiet Environment**
   - Minimize background noise
   - Close windows, turn off fans

4. **Complete Sentences**
   - Speak in full sentences
   - Pause 1-2 seconds between sentences

5. **Test Phrases**
   - "Hello, how are you today?"
   - "This is a test of the translation service."
   - "My name is [Your Name] and I live in [City]."

## 📞 Still Having Issues?

If you see the logs but no transcription:

1. **Check Deepgram API Key**
   ```bash
   grep DEEPGRAM_API_KEY .env
   # Should show your API key
   ```

2. **Check Deepgram Status**
   - Visit: https://status.deepgram.com
   - Ensure service is operational

3. **Check API Key Validity**
   - Visit: https://console.deepgram.com
   - Verify your API key is active

4. **Check Firewall/Network**
   - Ensure WebSocket connections allowed
   - Check corporate firewall settings

## 🎉 Success Indicators

You'll know it's working when you see:
- ✅ WebSocket connection opens
- 📤 Audio chunks being sent (every ~5 seconds)
- 📝 Partial transcripts appearing in real-time
- ✅ Final transcripts with proper punctuation
- 🌍 Translations appearing
- 🔊 Translated audio playing back

## 📝 Log Locations

- **Terminal output**: Where you ran uvicorn
- **server.log**: File in project directory
- **Browser console**: F12 in browser

---

**Ready to test! Open http://localhost:8000 and start speaking!** 🎤✨
