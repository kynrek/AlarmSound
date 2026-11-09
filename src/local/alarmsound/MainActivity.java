package local.alarmsound;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.media.AudioManager;
import android.os.Build;
import android.os.Bundle;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;

/** Settings + test screen. Opening it once after install also lets the app receive broadcasts. */
public class MainActivity extends Activity {
    static final int BG = 0xFF0F0E13, CARD = 0xFF1C1A23,
            LED = 0xFFFF453A, LED_DIM = 0x33FF453A, TEXT = 0xFFF5F3F7, MUTED = 0xFFA7A2B3;

    private LinearLayout root;
    private TextView priorityValue, urgentValue, alertVolumeValue, phoneVolumeValue, ceilingNote;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setBackgroundDrawable(new ColorDrawable(BG));
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(16), dp(8), dp(16), dp(24));
        final ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);
        scroll.addView(root);
        scroll.setClipToPadding(false);
        // Edge-to-edge (forced on Android 15+): keep content clear of the status / nav bars.
        scroll.setOnApplyWindowInsetsListener(new View.OnApplyWindowInsetsListener() {
            @Override public WindowInsets onApplyWindowInsets(View v, WindowInsets in) {
                int top, bottom;
                if (Build.VERSION.SDK_INT >= 30) {
                    android.graphics.Insets i = in.getInsets(WindowInsets.Type.systemBars());
                    top = i.top; bottom = i.bottom;
                } else {
                    top = in.getSystemWindowInsetTop(); bottom = in.getSystemWindowInsetBottom();
                }
                v.setPadding(0, top, 0, bottom);
                return in;
            }
        });
        setContentView(scroll);

        header();

        LinearLayout sounds = section("Sounds", "Tap to choose. Every sound previews when you pick it.");
        priorityValue = soundRow(sounds, "Priority alert", "Rings once", Prefs.PRIORITY_SOUND, true);
        divider(sounds);
        urgentValue = soundRow(sounds, "Urgent alert", "Repeats every 30 s until acknowledged", Prefs.URGENT_SOUND, false);

        LinearLayout vol = section("Volume", null);
        alertVolume(vol);
        divider(vol);
        phoneAlarmVolume(vol);

        LinearLayout opts = section("Behavior", null);
        switchRow(opts, "Speaker only", "Never play over Bluetooth or headphones", Prefs.SPEAKER_ONLY, Prefs.speakerOnly(this));
        divider(opts);
        switchRow(opts, "Speak the alert", "Read the alert text aloud after the sound", Prefs.SPEAK_TEXT, Prefs.speakText(this));

        LinearLayout test = section("Test", "Plays exactly what an alert from Home Assistant sounds like.");
        LinearLayout buttons = new LinearLayout(this);
        buttons.setOrientation(LinearLayout.HORIZONTAL);
        buttons.addView(pill("Priority", false, v ->
                Player.play(this, "priority", "Priority test. This is how a priority alert sounds.", null)), weighted(0, dp(6)));
        buttons.addView(pill("Urgent", true, v ->
                Player.play(this, "urgent", "Urgent test. This is how an urgent alert sounds.", null)), weighted(dp(6), 0));
        test.addView(buttons);

        TextView foot = text("Sounds are original effects in the style of classic consoles. "
                + "Uses the alarm stream, so alerts are heard on silent.", 13, MUTED, false);
        foot.setPadding(dp(4), dp(16), dp(4), 0);
        root.addView(foot);
    }

    // ---------- building blocks ----------

    private void header() {
        LinearLayout h = new LinearLayout(this);
        h.setOrientation(LinearLayout.VERTICAL);
        h.setPadding(dp(4), dp(20), dp(4), dp(12));
        TextView clock = text("12:00", 44, LED, true);
        clock.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));
        clock.setShadowLayer(dp(10), 0, 0, LED);
        clock.setLetterSpacing(0.08f);
        h.addView(clock);
        h.addView(text("Alarm Sound", 30, TEXT, true));
        TextView sub = text("Sounds for Home Assistant priority and urgent alerts", 16, MUTED, false);
        sub.setPadding(0, dp(2), 0, 0);
        h.addView(sub);
        root.addView(h);
    }

    /** A titled rounded card; returns its content container. */
    private LinearLayout section(String title, String hint) {
        TextView t = text(title.toUpperCase(), 13, LED, true);
        t.setLetterSpacing(0.12f);
        t.setPadding(dp(8), dp(22), dp(8), dp(8));
        root.addView(t);
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(14), dp(18), dp(14));
        card.setBackground(rounded(CARD, dp(22)));
        if (hint != null) {
            TextView h = text(hint, 14, MUTED, false);
            h.setPadding(0, 0, 0, dp(8));
            card.addView(h);
        }
        root.addView(card, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return card;
    }

    private TextView soundRow(LinearLayout parent, final String title, String sub, final String key, final boolean priority) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(10), 0, dp(10));
        row.setBackground(ripple(0x00000000, dp(14)));

        LinearLayout texts = new LinearLayout(this);
        texts.setOrientation(LinearLayout.VERTICAL);
        texts.addView(text(title, 20, TEXT, true));
        texts.addView(text(sub, 14, MUTED, false));
        final TextView value = text("", 17, LED, true);
        value.setPadding(0, dp(4), 0, 0);
        texts.addView(value);
        row.addView(texts, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));

        TextView play = circleButton("▶");
        play.setOnClickListener(v -> Player.play(this, priority ? Prefs.priority(this) : Prefs.urgent(this), null, null));
        row.addView(play);
        row.setOnClickListener(v -> pickSound(title, key, priority));
        parent.addView(row);
        value.setText(Sounds.label(priority ? Prefs.priority(this) : Prefs.urgent(this)) + "  ›");
        return value;
    }

    /** Grouped sound list in a dialog; tapping a row selects + previews it. */
    private void pickSound(String title, final String key, final boolean priority) {
        final String current = priority ? Prefs.priority(this) : Prefs.urgent(this);
        final LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        list.setPadding(dp(8), dp(4), dp(8), dp(8));
        final TextView[] rows = new TextView[Sounds.count()];
        int lastSection = -1;
        for (int i = 0; i < Sounds.count(); i++) {
            if (Sounds.section(i) != lastSection) {
                lastSection = Sounds.section(i);
                TextView h = text(Sounds.SECTIONS[lastSection].toUpperCase(), 12, LED, true);
                h.setLetterSpacing(0.1f);
                h.setPadding(dp(12), dp(16), dp(12), dp(6));
                list.addView(h);
            }
            final int idx = i;
            final TextView r = text("", 18, TEXT, false);
            r.setPadding(dp(14), dp(12), dp(14), dp(12));
            r.setOnClickListener(v -> {
                String id = Sounds.id(idx);
                Prefs.get(this).edit().putString(key, id).apply();
                for (int j = 0; j < rows.length; j++) styleChoice(rows[j], j, j == idx);
                (priority ? priorityValue : urgentValue).setText(Sounds.label(idx) + "  ›");
                Player.play(this, id, null, null);
            });
            rows[i] = r;
            styleChoice(r, i, Sounds.id(i).equals(current));
            list.addView(r, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        }
        ScrollView sv = new ScrollView(this);
        sv.addView(list);
        AlertDialog d = new AlertDialog.Builder(this, android.R.style.Theme_Material_Dialog_Alert)
                .setTitle(title + " sound")
                .setView(sv)
                .setPositiveButton("Done", null)
                .create();
        d.show();
        if (d.getWindow() != null) d.getWindow().setBackgroundDrawable(rounded(CARD, dp(24)));
        d.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(LED);
        d.getButton(AlertDialog.BUTTON_POSITIVE).setTextSize(17);
    }

    private void styleChoice(TextView r, int i, boolean selected) {
        r.setText((selected ? "●  " : "     ") + Sounds.label(i));
        r.setTextColor(selected ? LED : TEXT);
        r.setTypeface(selected ? Typeface.create("sans-serif-medium", Typeface.NORMAL) : Typeface.DEFAULT);
        r.setBackground(ripple(selected ? LED_DIM : 0x00000000, dp(14)));
    }

    private void alertVolume(LinearLayout parent) {
        final AudioManager am = getSystemService(AudioManager.class);
        final int max = am.getStreamMaxVolume(AudioManager.STREAM_ALARM);
        alertVolumeValue = sliderHeader(parent, "Alert volume", "How loud alerts play. 0 is half the phone's lowest step.");
        SeekBar bar = slider(max, Math.min(max, Prefs.volume(this)));
        alertVolumeValue.setText(ledNumber(Prefs.volume(this)));
        bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar s, int v, boolean user) { alertVolumeValue.setText(ledNumber(v)); }
            @Override public void onStartTrackingTouch(SeekBar s) {}
            @Override public void onStopTrackingTouch(SeekBar s) {
                Prefs.get(MainActivity.this).edit().putInt(Prefs.VOLUME, s.getProgress()).apply();
                Player.play(MainActivity.this, Prefs.priority(MainActivity.this), null, null);
            }
        });
        parent.addView(bar);
        ceilingNote = text(ceilingText(am, max), 13, MUTED, false);
        parent.addView(ceilingNote);
    }

    private void phoneAlarmVolume(LinearLayout parent) {
        final AudioManager am = getSystemService(AudioManager.class);
        final int max = am.getStreamMaxVolume(AudioManager.STREAM_ALARM);
        final int min = Math.max(1, am.getStreamMinVolume(AudioManager.STREAM_ALARM));
        phoneVolumeValue = sliderHeader(parent, "Phone alarm volume", "The phone's own setting. Also your alarm clock's volume.");
        SeekBar bar = slider(max - min, am.getStreamVolume(AudioManager.STREAM_ALARM) - min);
        phoneVolumeValue.setText(ledNumber(am.getStreamVolume(AudioManager.STREAM_ALARM)));
        bar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar s, int v, boolean user) { phoneVolumeValue.setText(ledNumber(v + min)); }
            @Override public void onStartTrackingTouch(SeekBar s) {}
            @Override public void onStopTrackingTouch(SeekBar s) {
                try {
                    am.setStreamVolume(AudioManager.STREAM_ALARM, s.getProgress() + min, AudioManager.FLAG_PLAY_SOUND);
                } catch (RuntimeException e) {
                    ceilingNote.setText("Could not change the phone alarm volume: " + e.getMessage());
                    return;
                }
                ceilingNote.setText(ceilingText(am, max));
            }
        });
        parent.addView(bar);
    }

    private String ceilingText(AudioManager am, int max) {
        return "Alerts can't be louder than the phone alarm volume (now "
                + am.getStreamVolume(AudioManager.STREAM_ALARM) + " of " + max + ").";
    }

    private TextView sliderHeader(LinearLayout parent, String title, String sub) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(10), 0, dp(4));
        LinearLayout texts = new LinearLayout(this);
        texts.setOrientation(LinearLayout.VERTICAL);
        texts.addView(text(title, 20, TEXT, true));
        texts.addView(text(sub, 14, MUTED, false));
        row.addView(texts, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        TextView value = text("", 30, LED, true);
        value.setTypeface(Typeface.create(Typeface.MONOSPACE, Typeface.BOLD));
        value.setShadowLayer(dp(6), 0, 0, LED);
        value.setPadding(dp(12), 0, 0, 0);
        row.addView(value);
        parent.addView(row);
        return value;
    }

    private SeekBar slider(int max, int value) {
        SeekBar s = new SeekBar(this);
        s.setMax(max);
        s.setProgress(value);
        s.setPadding(dp(8), dp(14), dp(8), dp(14));
        s.setProgressTintList(ColorStateList.valueOf(LED));
        s.setProgressBackgroundTintList(ColorStateList.valueOf(0xFF4A4655));
        s.setThumbTintList(ColorStateList.valueOf(LED));
        s.setMinimumHeight(dp(44));
        return s;
    }

    private void switchRow(LinearLayout parent, String title, String sub, final String key, boolean value) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(10), 0, dp(10));
        LinearLayout texts = new LinearLayout(this);
        texts.setOrientation(LinearLayout.VERTICAL);
        texts.addView(text(title, 20, TEXT, true));
        texts.addView(text(sub, 14, MUTED, false));
        row.addView(texts, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        final Switch sw = new Switch(this);
        sw.setChecked(value);
        int[][] states = {{android.R.attr.state_checked}, {}};
        sw.setThumbTintList(new ColorStateList(states, new int[]{LED, 0xFFCFCBD6}));
        sw.setTrackTintList(new ColorStateList(states, new int[]{0x88FF453A, 0xFF4A4655}));
        sw.setScaleX(1.2f);
        sw.setScaleY(1.2f);
        sw.setOnCheckedChangeListener((b, on) -> Prefs.get(this).edit().putBoolean(key, on).apply());
        row.addView(sw);
        row.setOnClickListener(v -> sw.toggle());
        parent.addView(row);
    }

    private void divider(LinearLayout parent) {
        View d = new View(this);
        d.setBackgroundColor(0xFF2E2B37);
        parent.addView(d, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, Math.max(1, dp(1))));
    }

    private TextView pill(String label, boolean filled, View.OnClickListener click) {
        TextView b = text(label, 18, filled ? Color.WHITE : LED, true);
        b.setGravity(Gravity.CENTER);
        b.setPadding(dp(12), dp(16), dp(12), dp(16));
        GradientDrawable shape = rounded(filled ? LED : 0x00000000, dp(28));
        if (!filled) shape.setStroke(dp(2), LED);
        b.setBackground(new RippleDrawable(ColorStateList.valueOf(0x55FFFFFF), shape, rounded(Color.WHITE, dp(28))));
        b.setOnClickListener(click);
        return b;
    }

    private TextView circleButton(String glyph) {
        TextView b = text(glyph, 18, LED, true);
        b.setGravity(Gravity.CENTER);
        GradientDrawable c = new GradientDrawable();
        c.setShape(GradientDrawable.OVAL);
        c.setColor(LED_DIM);
        GradientDrawable mask = new GradientDrawable();
        mask.setShape(GradientDrawable.OVAL);
        mask.setColor(Color.WHITE);
        b.setBackground(new RippleDrawable(ColorStateList.valueOf(0x55FF453A), c, mask));
        b.setLayoutParams(new LinearLayout.LayoutParams(dp(52), dp(52)));
        return b;
    }

    private LinearLayout.LayoutParams weighted(int left, int right) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        lp.setMargins(left, dp(4), right, dp(4));
        return lp;
    }

    private TextView text(String s, int sp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(TypedValue.COMPLEX_UNIT_SP, sp);
        t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        return t;
    }

    private GradientDrawable rounded(int color, int radius) {
        GradientDrawable g = new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(radius);
        return g;
    }

    private RippleDrawable ripple(int color, int radius) {
        return new RippleDrawable(ColorStateList.valueOf(0x33FFFFFF), rounded(color, radius), rounded(Color.WHITE, radius));
    }

    private static String ledNumber(int v) { return String.format("%02d", v); }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }
}
