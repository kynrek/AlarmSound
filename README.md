# Alarm Sound

A tiny Android app that makes Home Assistant alerts **audible even when the phone is on silent**.
When Home Assistant sends it a broadcast, it plays a short sound and then speaks the alert text. Both play on the
alarm stream, which silent, vibrate and Do Not Disturb don't block. By default they play on the phone's
built-in speaker only, never over Bluetooth or headphones.

It has no internet permission, analytics or background service. Android wakes the app only when a broadcast
arrives.

## Features
- **Two alert levels** (`priority`, `urgent`), each with its own sound.
- **60 built-in sounds in 9 sections:**
  - Classic alarms: beeps, chime, sirens, klaxon, bell.
  - Sound-chip-style effects and short tracks in the style of 8-bit and 16-bit consoles, Game Boy, N64 and
    GameCube eras.
  - Early-90s MT-32-style PC game jingles.
  - Family radio-drama style cues.
- **Spoken alert text** after the sound, using the phone's text-to-speech on the same speaker-only route.
- **Alert volume** (0–15), applied as playback gain so it works in the background. 0 is half as loud as the
  phone's lowest alarm step.
- **Phone alarm volume** slider, for convenience.
- Dark retro UI and an 80s LED alarm-clock icon.

All sounds are **original**. They're generated from code by [`tools/make_sounds.py`](tools/make_sounds.py) (Python
stdlib only) and imitate the *style* of classic sound hardware (pulse/triangle/noise channels, FM synthesis, 4-bit
wave, LA-synth-like instruments). They don't copy any game's actual sound effects or music.

## Home Assistant
The [companion app](https://companion.home-assistant.io/) sends the broadcast:

```yaml
action: notify.mobile_app_<your_phone>
data:
  message: command_broadcast_intent
  data:
    intent_package_name: local.alarmsound
    intent_action: local.alarmsound.PLAY
    # level: priority | urgent (or a sound id such as r_coin); text is URL-encoded
    intent_extras: "level:urgent,text:{{ ('Front door. Left open for 10 minutes') | urlencode }}"
```

Send your normal notification (with an Acknowledge action, if you want one) alongside it. For a "ring until
acknowledged" alert, repeat both every 30 s in a script until the `mobile_app_notification_action` event arrives.
[`examples/home-assistant-script.yaml`](examples/home-assistant-script.yaml) is a complete script that does both.

Post that notification on a **low-importance channel** (`channel: Alarm alert quiet`, `importance: low`), so it
makes no sound of its own. **Don't** use `channel: alarm_stream` for it. That channel plays the phone's default alarm
tone, so whenever the ringer is on normal you'd hear the alarm tone at the same time as Alarm Sound. A low-importance
notification doesn't pop up as a banner, but it shows in the shade and on the lock screen with its buttons. To get the
banner back, use a high-importance channel and set that channel's sound to *None* in the phone's notification
settings.

## Build
This repo has no Gradle. It uses the Android SDK's build tools directly (`aapt2`, `javac`, `d8`, `zipalign`,
`apksigner`) and needs build-tools 36.0.0, platform android-36 and JDK 17+.

    python3 tools/make_sounds.py          # regenerate res/raw/*.wav (the generated files are committed)
    ./build.sh                            # -> build/AlarmSound.apk
    ADB_SERIAL=<device> ./build.sh install

`build.sh` creates a signing key in `~/android-keys/` on its first run. The key is never stored in the repo. Keep
it: updates must be signed with the same key.

## Phone setup
1. Install the app, then **open it once**. A newly installed app can't receive broadcasts until it has been
   opened.
2. On **Xiaomi / HyperOS** (and similar), allow **Autostart**. Without it, the system blocks the broadcast while
   the app isn't running. HyperOS resets this a few seconds after every install or update, so
   `./build.sh install` re-applies and checks it:

       adb shell appops set local.alarmsound 10008 allow

3. Turn off **"Pause app activity if unused"**, so alerts don't stop after months without opening the app.
   `./build.sh install` does this too.

## Limitations
- Android blocks background apps from *raising* the system volume. Alerts can be at most as loud as the phone's
  alarm volume, and the app's alert volume only turns them down from there.
- Speaker-only routing uses `MediaPlayer.setPreferredDevice` with the built-in speaker. It's honored on the
  devices tested, but Android may still override it in some situations.

## License
MIT. See [LICENSE](LICENSE).
