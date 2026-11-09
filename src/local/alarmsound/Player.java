package local.alarmsound;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.media.AudioAttributes;
import android.media.AudioDeviceInfo;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.speech.tts.UtteranceProgressListener;
import android.util.Log;

import java.io.File;

/**
 * Plays an alert: the chosen sound, then (optionally) the alert text spoken aloud.
 * Volume: the app's own "alert volume" setting, applied as playback gain (see gain()).
 * Everything plays on the ALARM stream (audible on silent / vibrate / DND) and, by default,
 * is pinned to the phone's built-in speaker so it never goes to Bluetooth or headphones.
 */
final class Player {
    static final String TAG = "AlarmSound";
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static int seq = 0;

    private Player() {}

    /** level: "priority" | "urgent" | a sound id (for tests). text may be null. */
    static void play(Context ctx, String level, String text, BroadcastReceiver.PendingResult pending) {
        final Context app = ctx.getApplicationContext();
        String soundId = "urgent".equals(level) ? Prefs.urgent(app)
                : "priority".equals(level) ? Prefs.priority(app) : level;
        final int res = Sounds.res(soundId, R.raw.p_two_beeps);
        final boolean speak = text != null && !text.trim().isEmpty() && Prefs.speakText(app);
        final AudioManager am = app.getSystemService(AudioManager.class);

        final float gain = gain(app, am);
        final Runnable[] finish = new Runnable[1];
        finish[0] = new Runnable() {
            boolean ran = false;
            @Override public void run() {
                if (ran) return;
                ran = true;
                if (pending != null) pending.finish();
            }
        };
        // Safety net: never hold the broadcast forever.
        MAIN.postDelayed(finish[0], 45000);

        if (!speak) {
            playOne(app, am, res, null, gain, finish[0]);
            return;
        }
        // Synthesize the speech while the sound plays, then play it on the same (speaker) route.
        final File wav = new File(app.getCacheDir(), "tts-" + (seq++ % 4) + ".wav");
        final boolean[] soundDone = {false};
        final boolean[] speechReady = {false};
        final boolean[] speechFailed = {false};
        final Runnable maybeSpeak = new Runnable() {
            @Override public void run() {
                if (!soundDone[0] || !(speechReady[0] || speechFailed[0])) return;
                if (speechReady[0]) playOne(app, am, 0, wav, gain, finish[0]);
                else finish[0].run();
            }
        };
        final TextToSpeech[] tts = new TextToSpeech[1];
        tts[0] = new TextToSpeech(app, new TextToSpeech.OnInitListener() {
            @Override public void onInit(int status) {
                if (status != TextToSpeech.SUCCESS) {
                    Log.w(TAG, "TTS init failed: " + status);
                    speechFailed[0] = true; MAIN.post(maybeSpeak); return;
                }
                tts[0].setOnUtteranceProgressListener(new UtteranceProgressListener() {
                    @Override public void onStart(String id) {}
                    @Override public void onDone(String id) {
                        speechReady[0] = true; tts[0].shutdown(); MAIN.post(maybeSpeak);
                    }
                    @Override public void onError(String id) {
                        Log.w(TAG, "TTS synth error");
                        speechFailed[0] = true; tts[0].shutdown(); MAIN.post(maybeSpeak);
                    }
                });
                tts[0].synthesizeToFile(text.trim(), new Bundle(), wav, "alert");
            }
        });
        playOne(app, am, res, null, gain, new Runnable() {
            @Override public void run() { soundDone[0] = true; maybeSpeak.run(); }
        });
    }

    /**
     * Playback gain so the alert sounds like alarm-volume step N (the app's setting), whatever the
     * phone's alarm volume is. Step 0 = half as loud (-6 dB) as the lowest step. This only ever
     * attenuates (Android does not let a background app raise the system volume), so the phone's
     * alarm volume is the ceiling.
     */
    static float gain(Context app, AudioManager am) {
        int want = Prefs.volume(app);
        int min = Math.max(1, am.getStreamMinVolume(AudioManager.STREAM_ALARM));
        int max = am.getStreamMaxVolume(AudioManager.STREAM_ALARM);
        int cur = am.getStreamVolume(AudioManager.STREAM_ALARM);
        int target = Math.min(max, Math.max(min, want));
        float g = 1f;
        try {
            float dbCur = am.getStreamVolumeDb(AudioManager.STREAM_ALARM, Math.max(min, cur),
                    AudioDeviceInfo.TYPE_BUILTIN_SPEAKER);
            float dbWant = am.getStreamVolumeDb(AudioManager.STREAM_ALARM, target,
                    AudioDeviceInfo.TYPE_BUILTIN_SPEAKER);
            if (!Float.isInfinite(dbCur) && !Float.isNaN(dbCur) && !Float.isNaN(dbWant)) {
                g = (float) Math.pow(10, (dbWant - dbCur) / 20.0);
            } else if (cur > 0) {
                g = target / (float) cur;
            }
        } catch (RuntimeException e) {
            if (cur > 0) g = target / (float) cur;
        }
        if (want <= 0) g *= 0.5f;
        g = Math.max(0.02f, Math.min(1f, g));
        Log.i(TAG, "gain " + g + " (alert volume " + want + ", phone alarm volume " + cur + ")");
        return g;
    }

    /** Play a raw resource (res != 0) or a file, then run next. */
    private static void playOne(Context app, AudioManager am, int res, File file, float gain, final Runnable next) {
        final MediaPlayer mp = new MediaPlayer();
        final Runnable done = new Runnable() {
            boolean ran = false;
            @Override public void run() {
                if (ran) return;
                ran = true;
                try { mp.release(); } catch (RuntimeException ignored) {}
                next.run();
            }
        };
        try {
            mp.setAudioAttributes(new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(file != null ? AudioAttributes.CONTENT_TYPE_SPEECH
                            : AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build());
            if (file != null) {
                mp.setDataSource(file.getAbsolutePath());
            } else {
                AssetFileDescriptor afd = app.getResources().openRawResourceFd(res);
                mp.setDataSource(afd.getFileDescriptor(), afd.getStartOffset(), afd.getLength());
                afd.close();
            }
            if (Prefs.speakerOnly(app)) pinToSpeaker(mp, am);
            mp.prepare();
            mp.setVolume(gain, gain);
            mp.setOnCompletionListener(new MediaPlayer.OnCompletionListener() {
                @Override public void onCompletion(MediaPlayer p) { done.run(); }
            });
            mp.setOnErrorListener(new MediaPlayer.OnErrorListener() {
                @Override public boolean onError(MediaPlayer p, int what, int extra) {
                    Log.w(TAG, "playback error " + what + "/" + extra);
                    done.run();
                    return true;
                }
            });
            mp.start();
            Log.i(TAG, "playing " + (file != null ? "speech" : app.getResources().getResourceEntryName(res)));
        } catch (Exception e) {
            Log.e(TAG, "could not play", e);
            done.run();
        }
    }

    /** Route to the built-in speaker only (not Bluetooth / wired headphones). */
    private static void pinToSpeaker(MediaPlayer mp, AudioManager am) {
        for (AudioDeviceInfo d : am.getDevices(AudioManager.GET_DEVICES_OUTPUTS)) {
            if (d.getType() == AudioDeviceInfo.TYPE_BUILTIN_SPEAKER) {
                boolean ok = mp.setPreferredDevice(d);
                Log.i(TAG, "speaker-only route " + (ok ? "set" : "FAILED"));
                return;
            }
        }
        Log.w(TAG, "no built-in speaker found");
    }
}
