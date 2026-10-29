"""Synthesize an original, unobtrusive instrumental bed for the DriveTTO recut.

Usage:
    python generate_recut_music.py --seconds 100 --output music.wav --metadata music.json
    python generate_recut_music.py --seconds 184.25 --drive-start 51 --closing-start 170.25 --output long.wav --metadata long.json

Optional section markers override the default schedule. Longer edits scale the
51-second driving entrance and 170.25-second closing of the 184.25-second cut;
edits at or below 120 seconds retain the original short-cut schedule.

Only NumPy and the Python standard library are used. This is procedural music,
not sampled music or a professional mastering pipeline. Apply final loudness
normalization during video assembly (the intended delivery target is -20 LUFS).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import wave

import numpy as np


SAMPLE_RATE = 48_000
BPM = 96
SEED = 20261030
BEAT = 60.0 / BPM
CHORD_SECONDS = 16 * BEAT
# Original arrangement over common diatonic harmony; no quoted melody.
CHORDS = ((50, 54, 57, 61, 64), (47, 50, 54, 57, 61),
          (43, 47, 50, 54, 57), (45, 49, 52, 57, 59))


def hz(midi: float) -> float:
    return 440.0 * 2.0 ** ((midi - 69.0) / 12.0)


def section_markers(duration: float, drive_start: float | None,
                    closing_start: float | None) -> tuple[float, float]:
    if drive_start is None:
        drive_start = 40.0 if duration <= 120 else duration * (51.0 / 184.25)
    elif not math.isfinite(drive_start) or not 0 <= drive_start < duration:
        raise ValueError("--drive-start must be finite and within the audio duration")
    if closing_start is None:
        closing_start = (min(100.0, max(42.0, duration - 10.0)) if duration <= 120
                         else duration * (170.25 / 184.25))
    elif not math.isfinite(closing_start) or not 0 < closing_start <= duration:
        raise ValueError("--closing-start must be finite and within the audio duration")
    if closing_start <= drive_start:
        raise ValueError("Closing must follow the driving entrance")
    return float(drive_start), float(closing_start)


def section_level(time: float, drive_start: float, closing_start: float) -> float:
    """Smoothly increase the driving section and soften the closing section."""
    activity = 0.66 + 0.34 * np.clip((time - (drive_start - 2.0)) / 5.0, 0.0, 1.0)
    closing = 1.0 - 0.40 * np.clip((time - closing_start) / 8.0, 0.0, 1.0)
    return float(activity * closing)


def add_stereo(audio: np.ndarray, start: float, sound: np.ndarray, pan: float = 0.0) -> None:
    first = max(0, round(start * SAMPLE_RATE))
    end = min(len(audio), first + len(sound))
    if end <= first:
        return
    sound = sound[:end - first]
    if sound.ndim == 2:
        audio[first:end] += sound
    else:
        angle = (float(np.clip(pan, -1.0, 1.0)) + 1.0) * math.pi / 4.0
        audio[first:end, 0] += sound * math.cos(angle)
        audio[first:end, 1] += sound * math.sin(angle)


def render_music(seconds: float, drive_start: float | None = None,
                 closing_start: float | None = None) -> tuple[np.ndarray, dict]:
    if not math.isfinite(seconds) or not 0.1 <= seconds <= 600:
        raise ValueError("--seconds must be finite and between 0.1 and 600")
    count = round(seconds * SAMPLE_RATE)
    actual_seconds = count / SAMPLE_RATE
    drive_start, closing_start = section_markers(actual_seconds, drive_start, closing_start)
    rng = np.random.default_rng(SEED)
    audio = np.zeros((count, 2), dtype=np.float32)
    events = {"pad_chords": 0, "bass_notes": 0, "soft_bell_notes": 0,
              "kick_hits": 0, "shaker_hits": 0}

    # Slow, overlapping pads. Small left/right detuning gives width without a
    # feedback or delay process that could complicate the deterministic render.
    for chord_index, start in enumerate(np.arange(0.0, actual_seconds, CHORD_SECONDS)):
        chord = CHORDS[chord_index % len(CHORDS)]
        length = min(CHORD_SECONDS + 2.4, actual_seconds - float(start))
        t = np.arange(round(length * SAMPLE_RATE), dtype=np.float32) / SAMPLE_RATE
        attack = np.sin(np.clip(t / 1.8, 0, 1) * math.pi / 2) ** 2
        release = np.sin(np.clip((length - t) / 2.8, 0, 1) * math.pi / 2) ** 2
        env = attack * release
        chord_sound = np.zeros((len(t), 2), dtype=np.float32)
        for note in chord:
            phase = float(rng.uniform(0, 2 * math.pi))
            for channel, cents in enumerate((-2.0, 2.0)):
                f = hz(note) * 2 ** (cents / 1200.0)
                oscillator = (np.sin(2 * math.pi * f * t + phase)
                              + 0.16 * np.sin(2 * math.pi * 2 * f * t + phase * 0.7)
                              + 0.05 * np.sin(2 * math.pi * 3 * f * t + phase * 1.1))
                tremolo = 0.96 + 0.04 * np.sin(2 * math.pi * 0.12 * t + phase)
                chord_sound[:, channel] += oscillator * env * tremolo * 0.012
        add_stereo(audio, float(start), chord_sound)
        events["pad_chords"] += 1

    for beat_index, start in enumerate(np.arange(0.0, actual_seconds, BEAT)):
        start = float(start)
        level = section_level(start, drive_start, closing_start)
        chord = CHORDS[int(start // CHORD_SECONDS) % len(CHORDS)]
        driving = drive_start <= start < min(closing_start, actual_seconds - 5.0)

        # Warm rounded bass on the start and middle of each bar.
        if beat_index % 4 in (0, 2):
            length = 0.85 if beat_index % 4 == 0 else 0.55
            t = np.arange(round(length * SAMPLE_RATE), dtype=np.float32) / SAMPLE_RATE
            f = hz(chord[0] - 12)
            env = (1 - np.exp(-t / 0.025)) * np.exp(-t / 0.30)
            env *= np.clip((length - t) / 0.10, 0, 1)
            sound = (np.sin(2 * math.pi * f * t) + 0.13 * np.sin(4 * math.pi * f * t)) * env
            add_stereo(audio, start, sound * 0.075 * level)
            events["bass_notes"] += 1

        # One restrained kick per bar; a second appears in the driving section.
        if beat_index % 4 == 0 or (driving and beat_index % 4 == 2):
            t = np.arange(round(0.22 * SAMPLE_RATE), dtype=np.float32) / SAMPLE_RATE
            frequency = 44.0 + 48.0 * np.exp(-t / 0.020)
            phase = 2 * math.pi * np.cumsum(frequency, dtype=np.float64) / SAMPLE_RATE
            env = (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.053)
            add_stereo(audio, start, np.sin(phase).astype(np.float32) * env * 0.065 * level)
            events["kick_hits"] += 1

        # Quiet filtered noise, never a sharp clap or prominent snare.
        if beat_index % 2 == 1:
            n = round(0.065 * SAMPLE_RATE)
            t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
            noise = rng.standard_normal(n).astype(np.float32)
            smooth = np.convolve(noise, np.ones(7, dtype=np.float32) / 7, mode="same")
            env = (1 - np.exp(-t / 0.003)) * np.exp(-t / 0.018)
            add_stereo(audio, start + BEAT * 0.5, smooth * env * 0.022 * level,
                       pan=0.20 if beat_index % 4 == 1 else -0.20)
            events["shaker_hits"] += 1

        # Sparse harmonic sparks, denser only over driving. A deterministic
        # choice among chord tones avoids a recognizable quoted lead melody.
        spacing = 2 if driving else 4
        if beat_index % spacing == 0:
            note = chord[int(rng.integers(1, len(chord)))] + 12
            length = 1.2
            t = np.arange(round(length * SAMPLE_RATE), dtype=np.float32) / SAMPLE_RATE
            f = hz(note)
            env = (1 - np.exp(-t / 0.012)) * np.exp(-t / 0.32)
            env *= np.clip((length - t) / 0.18, 0, 1)
            sound = (np.sin(2 * math.pi * f * t)
                     + 0.18 * np.sin(2 * math.pi * f * 2.01 * t)) * env
            add_stereo(audio, start + 0.07, sound * 0.014 * level,
                       pan=float(rng.uniform(-0.45, 0.45)))
            events["soft_bell_notes"] += 1

    t = np.arange(count, dtype=np.float32) / SAMPLE_RATE
    fade_in = np.sin(np.clip(t / 2.0, 0, 1) * math.pi / 2) ** 2
    remaining = (count - 1 - np.arange(count, dtype=np.float32)) / SAMPLE_RATE
    fade_out = np.sin(np.clip(remaining / 3.0, 0, 1) * math.pi / 2) ** 2
    section = 0.66 + 0.34 * np.clip((t - (drive_start - 2.0)) / 5.0, 0, 1)
    section *= 1 - 0.40 * np.clip((t - closing_start) / 8.0, 0, 1)
    audio *= (fade_in * fade_out * section)[:, None]
    audio -= np.mean(audio, axis=0, dtype=np.float64).astype(np.float32)
    # Reapply the exact endpoint fade after DC removal so both ends are silent.
    audio *= (fade_in * fade_out)[:, None]
    raw_peak = float(np.max(np.abs(audio)))
    gain = min(0.72 / raw_peak, 4.0) if raw_peak > 0 else 1.0
    audio *= gain
    assert np.all(np.isfinite(audio))
    assert float(np.max(np.abs(audio))) <= 0.800001
    details = {"original_procedural_synthesis": True, "source_audio_samples": [],
               "vocals": False, "seed": SEED, "bpm": BPM,
               "sample_rate_hz": SAMPLE_RATE, "channels": 2,
               "requested_duration_seconds": seconds, "duration_seconds": actual_seconds,
               "sample_frames": count, "fade_in_seconds": 2.0, "fade_out_seconds": 3.0,
               "drive_start_seconds": drive_start, "closing_start_seconds": closing_start,
               "section_design": {"before_drive_start": "restrained pads, sparse bass and percussion",
                                  "drive_start_to_closing_start": "slightly stronger pulse and harmonic accents",
                                  "after_closing_start": "softer final section"},
               "events": events, "render_gain": gain,
               "mastering": "Unmastered synthesized music bed; final video assembly should normalize to -20 LUFS."}
    return audio, details


def write_music(seconds: float, output: Path, metadata: Path,
                drive_start: float | None = None, closing_start: float | None = None) -> dict:
    output, metadata = Path(output), Path(metadata)
    if output.resolve() == metadata.resolve():
        raise ValueError("Audio and metadata must use distinct paths")
    if output.exists() or metadata.exists():
        raise FileExistsError("Refusing to overwrite an existing audio file or metadata")
    output.parent.mkdir(parents=True, exist_ok=True)
    metadata.parent.mkdir(parents=True, exist_ok=True)
    samples, details = render_music(seconds, drive_start, closing_start)
    pcm = np.rint(samples * 32767.0).astype("<i2")
    decoded = pcm.astype(np.float64) / 32768.0
    peak = float(np.max(np.abs(decoded)))
    rms = float(np.sqrt(np.mean(decoded ** 2)))
    assert peak <= 0.8 and not np.any(np.abs(pcm.astype(np.int32)) >= 32767)
    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())
    details.update({"format": "PCM signed 16-bit little-endian WAV", "peak": peak,
                    "rms": rms, "rms_dbfs": 20 * math.log10(rms) if rms > 0 else None,
                    "clipped_samples": 0, "bytes": output.stat().st_size,
                    "sha256": hashlib.sha256(output.read_bytes()).hexdigest()})
    metadata.write_text(json.dumps(details, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return details


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seconds", required=True, type=float)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--drive-start", type=float, default=None,
                        help="Seconds at which the stronger driving pulse starts (duration-adaptive default)")
    parser.add_argument("--closing-start", type=float, default=None,
                        help="Seconds at which the closing section softens (duration-adaptive default)")
    args = parser.parse_args()
    print(json.dumps(write_music(args.seconds, args.output, args.metadata,
                                 args.drive_start, args.closing_start), ensure_ascii=False))


if __name__ == "__main__":
    main()
