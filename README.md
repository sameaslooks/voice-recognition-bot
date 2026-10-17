# Local Voice Recognition Telegram Bot

A local Telegram bot for transcribing voice messages built on **GigaAM v3 e2e RNNT** (ONNX int8) and the `sherpa-onnx` engine.

It was designed to run on low-resource hardware (like a Raspberry Pi) and for private use. No paid APIs, no monthly bills, and no audio data ever leaves your server.

## Features

- **Local ASR:** GigaAM handles Russian speech perfectly and automatically adds punctuation and capitalization.
- **Smart Memory Management:** The model loads into RAM only on the first request. If it's not used for a set time, it unloads to free up RAM for other services.
- **Request Queue:** If multiple users send voice messages at once, they are queued. This protects low-end CPUs from resource spikes and crashes.
- **Access Control:** The first user to send `/start` becomes the admin. Others wait for approval.
- **Group Support:** The bot can be added to groups. If invited by an approved user, it transcribes voice messages for all group members.
- **Privacy-First Stats:** Only usage metrics (duration, file size) are collected. Message texts are never saved.
- **Dockerized:** Deploys in a couple of commands via `docker compose`.

## How it works

1. You send a voice message.
2. The bot downloads the OGG file and puts a task into the queue (`asyncio.Queue`).
3. A background worker picks up the task, converts the audio to 16 kHz mono WAV using `ffmpeg`, and splits it into chunks of `MAX_SEGMENT_SEC` seconds.
4. The chunks are processed by the model via `sherpa-onnx`.
5. If the model is unloaded, it is loaded into RAM first. After `MODEL_IDLE_TIMEOUT` seconds of inactivity, it is removed from memory.
6. The recognized text is sent back to the chat.

## Requirements

- Docker with Compose v2
- ~500 MB of RAM for the loaded model
- `ffmpeg` (installed inside the Docker image)
- ~230 MB of free disk space for model files (downloaded automatically on the first run)

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/sameaslooks/voice-recognition-bot.git
cd voice-recognition-bot
```

### 2. Configure environment
Copy the example config and set your bot token:
```bash
cp .env.example .env
cp docker-compose.yml.example docker-compose.yml
nano .env
```

You must fill in the `BOT_TOKEN` (get it from [@BotFather](https://t.me/BotFather)).
Also you may change the global bot language between English and Russian by changing `LANGUAGE` setting to either `EN` or `RU`.

### 3. Create directories
Create directories for the database and models:
```bash
mkdir -p data models
```

### 4. Run the bot
```bash
docker compose up -d --build
docker compose logs -f
```

On the first run, the bot will automatically download the required model files from HuggingFace into the `./models` folder.

### 5. Claim Admin
Open the bot in Telegram and send `/start`. The first user gets the `admin` role automatically.

## Configuration (`.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BOT_TOKEN` | — | Telegram bot token (required) |
| `NUM_THREADS` | `2` | Number of CPU threads for inference. `2` is optimal for 4-core ARM boards. |
| `MAX_SEGMENT_SEC` | `25` | Maximum audio chunk length in seconds. GigaAM loses quality on long files, `20-25` is the sweet spot. |
| `MODEL_IDLE_TIMEOUT` | `1800` | Time in seconds (30 minutes) after which the model is unloaded from memory when idle. |

## Group Usage Setup

To make the bot work in groups:

1. Go to [@BotFather](https://t.me/BotFather) -> `/mybots` -> your bot -> `Bot Settings` -> `Group Privacy` -> click **Turn off**.
2. Add the bot to a group from a user account that has `admin` or `user` rights in the bot's database.
3. The bot will verify the inviter's rights and start transcribing voice messages from all group members.

## Admin Panel

The `/admin` command opens a menu where you can:
- View access requests.
- Approve, block, and promote users.
- View global and personal statistics on the number and duration of processed messages. (The last admin cannot be blocked).

## Data and Backups

- **Database:** The SQLite file is located at `./data/bot.db`.
- **Models:** Located in `./models`.

To back up the database, simply stop the container and copy the file:
```bash
docker compose stop
cp data/bot.db data/bot-backup.db
docker compose start
```

## Tips for Russian Users

If building Docker images from official mirrors is too slow, you can pass arguments during the build to use local mirrors (the `Dockerfile` supports `APT_MIRROR` and `PIP_INDEX_URL` arguments):

```bash
docker compose build --build-arg APT_MIRROR=mirror.yandex.ru --build-arg PIP_INDEX_URL=https://pypi-mirror.gitverse.ru/simple/
```

## Credits

- [GigaAM v3](https://huggingface.co/Alexxerm/gigaam-v3-e2e-rnnt-sherpa-onnx) by SberDevices.
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) for the blazing fast inference engine.

## License

GNU General Public License v3.0 (GPLv3).