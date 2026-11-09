package local.alarmsound;

import android.content.Context;
import android.content.SharedPreferences;

/** User settings (edited in MainActivity). Keys carry a version so changed defaults take effect. */
final class Prefs {
    static final String PRIORITY_SOUND = "priority_sound_v2";
    static final String URGENT_SOUND = "urgent_sound_v2";
    /** Alert volume 0..15 (alarm-volume steps). 0 = half as loud as the lowest step. */
    static final String VOLUME = "alert_volume_v2";
    static final String SPEAKER_ONLY = "speaker_only";
    static final String SPEAK_TEXT = "speak_text";

    static SharedPreferences get(Context c) {
        return c.getApplicationContext().getSharedPreferences("settings", Context.MODE_PRIVATE);
    }

    static String priority(Context c) { return get(c).getString(PRIORITY_SOUND, "r_ring"); }
    static String urgent(Context c) { return get(c).getString(URGENT_SOUND, "r_coin"); }
    static int volume(Context c) { return get(c).getInt(VOLUME, 0); }
    static boolean speakerOnly(Context c) { return get(c).getBoolean(SPEAKER_ONLY, true); }
    static boolean speakText(Context c) { return get(c).getBoolean(SPEAK_TEXT, true); }

    private Prefs() {}
}
