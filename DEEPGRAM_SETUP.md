# 🚀 Deepgram Setup Guide

## Why Deepgram?

**Deepgram provides significantly better transcription accuracy than AWS Transcribe:**
- ✅ **Better accuracy** (5-15% improvement)
- ✅ **Nova-2 model** - State-of-the-art speech recognition
- ✅ **Better with accents** and background noise
- ✅ **Automatic punctuation** and smart formatting
- ✅ **More affordable** than AWS Transcribe
- ✅ **Faster processing** with lower latency

## 📝 Quick Setup (5 minutes)

### Step 1: Get Deepgram API Key

1. **Sign up** at https://console.deepgram.com
   - Free tier: $200 credit (45+ hours of audio)
   - No credit card required

2. **Create API Key**:
   - Go to https://console.deepgram.com/project/default/keys
   - Click "Create New Key"
   - Copy your API key (starts with something like `abc123...`)

### Step 2: Add to .env File

Open your `.env` file and add:

```env
# Deepgram Configuration
DEEPGRAM_API_KEY=your_api_key_here
TRANSCRIPTION_PROVIDER=deepgram
```

Your `.env` should now look like:
```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here

# Deepgram (Better Accuracy)
DEEPGRAM_API_KEY=your_deepgram_api_key_here
TRANSCRIPTION_PROVIDER=deepgram
```

### Step 3: Install Deepgram SDK

```bash
pip3 install deepgram-sdk
```

### Step 4: Restart Server

```bash
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Step 5: Test!

Open `http://localhost:8000` and try speaking. You should see:
- ✅ Much better transcription accuracy
- ✅ Proper punctuation automatically
- ✅ Better handling of pauses and hesitations

## 🔄 Switch Back to AWS (Optional)

If you want to switch back to AWS Transcribe:

In `.env`:
```env
TRANSCRIPTION_PROVIDER=aws
```

Restart the server.

## 📊 Accuracy Comparison

| Provider | Clear Speech | Noisy | Accents | Technical Terms |
|----------|--------------|-------|---------|-----------------|
| **Deepgram Nova-2** | **95-98%** | **85-90%** | **85-92%** | **90-95%** |
| AWS Transcribe | 85-90% | 70-80% | 70-85% | 70-80% |

## 💰 Pricing Comparison

| Provider | Cost per Hour | Free Tier |
|----------|---------------|-----------|
| **Deepgram** | **$0.0043/min** ($0.26/hr) | $200 credit |
| AWS Transcribe | $0.024/min ($1.44/hr) | None |

**Deepgram is ~5.5x cheaper!**

## 🎯 Deepgram Features

### What's Included:
- ✅ **Nova-2 Model** - Most accurate model
- ✅ **Automatic Punctuation** - Proper commas, periods, etc.
- ✅ **Smart Formatting** - Numbers, dates, times formatted correctly
- ✅ **Utterance Detection** - Automatic sentence boundaries
- ✅ **Interim Results** - Real-time partial transcripts
- ✅ **Multi-language** - 30+ languages supported

### Languages Supported:
- English (US, UK, AU, IN)
- Spanish (Spain, Latin America)
- French, German, Italian, Portuguese
- Japanese, Korean, Chinese (Mandarin)
- Dutch, Russian, Turkish, Polish
- And many more!

## 🔧 Advanced Configuration (Optional)

### Custom Models

Deepgram offers specialized models:

```python
# In deepgram_transcribe_service.py, change model:
options = LiveOptions(
    model="nova-2",  # Default (best general purpose)
    # model="nova-2-medical",  # For medical conversations
    # model="nova-2-phonecall",  # For phone audio
    # model="nova-2-meeting",  # For meetings/conferences
    ...
)
```

### Adjust Sensitivity

```python
options = LiveOptions(
    utterance_end_ms=1000,  # Lower = more responsive (500-2000)
    endpointing=300,  # Speech detection sensitivity (100-500)
    ...
)
```

## 🐛 Troubleshooting

### "API Key not found"
- Check your `.env` file has `DEEPGRAM_API_KEY=...`
- Make sure there are no spaces around the `=`
- Restart the server after adding the key

### "Connection failed"
- Check your internet connection
- Verify API key is correct at https://console.deepgram.com
- Check Deepgram status: https://status.deepgram.com

### Still bad accuracy?
- Check microphone quality
- Reduce background noise
- Speak clearly at normal pace
- Check internet connection stability

## 📚 Resources

- **Deepgram Console**: https://console.deepgram.com
- **Documentation**: https://developers.deepgram.com
- **API Reference**: https://developers.deepgram.com/reference
- **Pricing**: https://deepgram.com/pricing

## 💡 Tips for Best Results

1. **Good Microphone**: Use a quality mic (headset recommended)
2. **Quiet Environment**: Minimize background noise
3. **Clear Speech**: Speak naturally, not too fast
4. **Stable Internet**: Good connection = better streaming
5. **Position**: Mic 6-12 inches from mouth

## ✨ Expected Results

With Deepgram, you should see:
- ✅ **95%+ accuracy** in good conditions
- ✅ **Proper punctuation** automatically added
- ✅ **Better real-time performance** (< 300ms latency)
- ✅ **Fewer errors** with technical terms
- ✅ **Better with accents** and dialects

## 🎉 That's It!

You're now using the most accurate transcription service available. Enjoy the improved accuracy! 🚀
