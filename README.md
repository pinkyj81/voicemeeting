# Voice Meeting Translator (KR <-> JP)

한국어/일본어 화자가 실시간 텍스트 입력 후 상호 번역하고, 번역 결과를 음성으로 재생하는 Flask 웹앱입니다.

## Features
- ✅ 한국어/일본어 텍스트 입력
- ✅ 양방향 자동 번역 (KR↔JP)
- ✅ 번역 결과 TTS 음성 재생
- ✅ PC/브라우저용 음성인식 모드 (Chrome/Edge)
- ✅ iPhone Safari 전용 텍스트 입력 모드

## System Requirements
- Python 3.8+
- Internet connection (for Google Translate API)
- Modern browser (Chrome/Edge recommended for voice features)

## Installation

### 1. Clone / Download
```bash
git clone https://github.com/YOUR_USERNAME/VoiceMeetingTranslator.git
cd VoiceMeetingTranslator
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Local Development
```bash
python app.py
```
- Browser: http://127.0.0.1:5055
- iPhone on same LAN: http://YOUR_PC_IP:5055/iphone

### Production Deployment
Set environment variables before running:

```bash
# Linux/macOS
export PORT=8080
export DEBUG=False
python app.py

# Windows PowerShell
$env:PORT="8080"
$env:DEBUG="False"
python app.py

# Docker (optional)
docker build -t voice-translator .
docker run -p 8080:8080 -e PORT=8080 voice-translator
```

## Configuration

Environment variables:
- `PORT`: Server port (default: 5055)
- `DEBUG`: Debug mode on/off (default: True)

## Architecture

```
/api/translate (POST)
  Input: { text, source, target }
  Output: { translated_text }

Routes:
  /           → PC/browser version (WebSpeech + text)
  /iphone     → iPhone Safari version (text-only)
```

## API Example
```bash
curl -X POST http://127.0.0.1:5055/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"안녕하세요","source":"ko","target":"ja"}'
```

Response:
```json
{"translated_text":"こんにちは"}
```

## Deployment Examples

### Render.com
1. Connect GitHub repo
2. Set environment:
   - PORT: 10000
   - DEBUG: False
3. Deploy

### Heroku (legacy/alternatives)
```bash
heroku create your-app-name
git push heroku main
```

### Self-hosted (AWS/GCP/Azure)
1. SSH into server
2. Clone repo, setup venv, install deps
3. Run with port 80/443 via nginx reverse proxy

## Known Limitations
- iPhone Safari: No browser Web Speech API → use text input + keyboard mic
- Translation quality: Depends on Google Translate API
- Requires internet connection for translation

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Can't connect on iPhone" | Ensure firewall allows port 5055, same LAN |
| "Translation API error" | Check internet connection, API rate limits |
| "No sound" | Enable browser/system audio, check TTS voice availability |

## License
MIT (optional - specify your license)

## Contributing
Pull requests welcome!

