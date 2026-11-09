package local.alarmsound;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;

/**
 * Receives local.alarmsound.PLAY. Extras (strings):
 *   level = "priority" | "urgent"   (which configured sound to play; default priority)
 *   text  = URL-encoded alert text to speak after the sound (optional)
 * Legacy: sound = a sound id, e.g. "u_siren".
 */
public class PlayReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        String level = intent.getStringExtra("level");
        if (level == null) level = intent.getStringExtra("sound");
        if (level == null) level = "priority";
        String text = intent.getStringExtra("text");
        if (text != null) text = Uri.decode(text.replace('+', ' '));
        Player.play(context, level.trim(), text, goAsync());
    }
}
