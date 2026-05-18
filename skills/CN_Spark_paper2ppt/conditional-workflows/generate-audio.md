---
description: Generate per-slide narration audio from speaker notes, then optionally re-export PPTX with embedded audio and timings.
---

# Generate Audio Workflow
document explanation(It doesn't affect the process, it only helps with understanding）：本文件在用户要求生成旁白、音频、录制 PPT 或带配音视频时读取；它从 notes/total.md 或 notes/*.md 生成每页音频，并可重新导出带录制旁白和自动翻页计时的 PPTX。

Standalone post-export workflow. Run when the user asks for narration audio, recorded PPT, voice-over, narrated video export, or similar. The workflow reads speaker notes, generates one audio file per slide, and optionally re-exports PPTX with embedded audio and auto-advance timings.

## When To Run

Run when:

- `<project_path>/notes/total.md` exists, or per-slide notes exist under `<project_path>/notes/`;
- the deck has reached the notes stage;
- the user asks for audio, narration, TTS, video-ready PPTX, or recorded presentation.

If per-slide notes are missing, split the master notes first:

```bash
python3 scripts/total_md_split.py <project_path>
```

Do not generate one long audio track for the whole deck. The contract is one notes file to one audio file to one slide.

## Audio Format Constraints

PowerPoint-reliable audio formats:

- `mp3`;
- `m4a` with AAC;
- `wav`.

Provider formats such as `pcm`, `opus`, or `flac` must be transcoded before embedding. Recorded narration export requires `ffprobe` so slide durations can be read from actual audio files.

Recorded narration cannot be combined with `on-click` object animations. Use `after-previous` or `with-previous`.

## Step 1 - Determine Language And Academic Tone

Read notes and determine the dominant spoken language. For Chinese academic decks, default to `zh-CN` unless context clearly indicates `zh-TW`, `zh-HK`, or another locale.

Mixed-language decks should use the language the audience will hear most. Preserve English technical terms in speech, but keep the voice locale aligned with the main narration language.

Academic narration style:

- formal but natural;
- no exaggerated performance tone;
- clear pace for formulas and citations;
- slightly slower for dense result, formula, and TechnicalRoute pages;
- do not read full GB/T 7714 citation entries aloud.

## Step 2 - Choose Backend And Voice Catalog

Default backend: `edge`.

Use cloud providers only when the user explicitly requests higher-quality cloud narration, cloned voice, or a provider-specific voice id.

List voices:

```bash
python3 scripts/notes_to_audio.py --list-voices --locale <locale>
```

Cloud providers:

```bash
python3 scripts/notes_to_audio.py --provider elevenlabs --list-voices
python3 scripts/notes_to_audio.py --provider minimax --list-voices
python3 scripts/notes_to_audio.py --provider qwen --list-voices
python3 scripts/notes_to_audio.py --provider cosyvoice --list-voices
```

Provider prerequisites:

- ElevenLabs: `ELEVENLABS_API_KEY`;
- MiniMax: `MINIMAX_API_KEY`;
- Qwen: `QWEN_API_KEY` or `DASHSCOPE_API_KEY`;
- CosyVoice: `COSYVOICE_API_KEY` or `DASHSCOPE_API_KEY`.

API keys may live in the current environment or a `.env` file supported by `notes_to_audio.py`.

## Step 3 - Recommend A Single Configuration

Ask once, with recommended values:

- provider;
- voice;
- rate or provider style settings;
- whether to embed audio into PPTX.

Default recommendations for Chinese academic PPT:

- provider: `edge` unless the user requested a cloud voice;
- voice: a clear Mandarin neural voice suitable for academic reporting;
- rate: `+0%` for ordinary notes, `-5%` for dense formula / review decks, `+5%` only for very short notes;
- embed audio: yes, unless the user wants separate audio files only.

If the user provided a cloned voice id and provider, skip the candidate list and confirm only rate and embedding.

## Step 4 - Execute

Edge default:

```bash
python3 scripts/notes_to_audio.py <project_path> --voice <chosen_voice> --rate <chosen_rate>
```

ElevenLabs:

```bash
python3 scripts/notes_to_audio.py <project_path> --provider elevenlabs --voice-id <voice_id> --elevenlabs-model eleven_multilingual_v2
```

MiniMax:

```bash
python3 scripts/notes_to_audio.py <project_path> --provider minimax --voice-id <voice_id> --minimax-model speech-2.8-hd
```

Qwen:

```bash
python3 scripts/notes_to_audio.py <project_path> --provider qwen --voice-id <voice> --qwen-model qwen3-tts-flash --qwen-language-type Chinese
```

CosyVoice:

```bash
python3 scripts/notes_to_audio.py <project_path> --provider cosyvoice --voice-id <voice> --cosyvoice-model cosyvoice-v3-flash
```

If the user chose embedding:

```bash
python3 scripts/svg_to_pptx.py <project_path> --recorded-narration audio
```

If any command reports a missing dependency, missing API key, unsupported audio format, or unreadable duration, fix the prerequisite and rerun. Do not continue with partial audio unless the user accepts it.

## Step 5 - Academic Narration QA

Before finalizing:

- every slide has a matching audio file;
- audio duration is readable;
- notes do not include Markdown headings, stage directions, or checklist labels in the spoken body;
- formula pages explain variable roles rather than reading symbols mechanically;
- reference pages are summarized; full citations are not read line by line;
- TechnicalRoute pages explain the route stages in order;
- recorded PPTX does not use `on-click` animations.

## Completion Report

Report:

- number of audio files generated;
- audio folder path;
- provider, voice, and rate/settings used;
- narrated PPTX path if embedded;
- if not embedded, the command to embed later.
