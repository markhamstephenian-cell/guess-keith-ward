# Guess Keith Ward

A cosmic-themed theological quiz exploring the mind of Keith Ward, one of Britain's greatest living theologians.

## Features

- 31 deep theological questions extracted from Ward's conversations
- 5 answer choices per question representing different Christian traditions
- Cosmic/supernatural UI with starfield animations
- Emoji celebrations for correct answers
- Read Ward's full responses after guessing

## Run Locally

```bash
cd ward-quiz/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000

## Tech Stack

- **Backend**: FastAPI, Python
- **Frontend**: Vanilla JS, CSS with cosmic theme
- **Data**: Questions extracted from Ward Conversation document

## Deploy to Railway

1. Connect this repo to [Railway](https://railway.app)
2. Set root directory to `ward-quiz`
3. Railway will auto-detect and deploy

## License

MIT
