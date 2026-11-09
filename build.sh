#!/bin/bash
# Build + sign AlarmSound without Gradle, using only Android SDK tools.
#   ./build.sh            -> build/AlarmSound.apk
#   ./build.sh install    -> also adb install --no-incremental to every connected phone (or $ADB_SERIAL)
# Signing key: ~/android-keys/alarmsound.jks (+ .pass), outside the repo. Created on first run; keep it (updates need the same key).
set -euo pipefail
cd "$(dirname "$0")"
SDK=${ANDROID_HOME:-$HOME/Android/Sdk}
BT=$SDK/build-tools/36.0.0
JAR=$SDK/platforms/android-36/android.jar
VERSION_CODE=${VERSION_CODE:-1}; VERSION_NAME=${VERSION_NAME:-1.0}
KEYDIR=$HOME/android-keys; KS=$KEYDIR/alarmsound.jks; KP=$KEYDIR/alarmsound.pass
rm -rf build && mkdir -p build/gen build/classes build/dex
"$BT/aapt2" compile --dir res -o build/res.zip
"$BT/aapt2" link -I "$JAR" --manifest AndroidManifest.xml --java build/gen \
  --min-sdk-version 26 --target-sdk-version 36 \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
  -o build/unsigned.apk build/res.zip
javac -source 11 -target 11 -Xlint:-options -encoding UTF-8 -classpath "$JAR" -d build/classes \
  $(find src build/gen -name '*.java')
"$BT/d8" --release --min-api 26 --lib "$JAR" --output build/dex $(find build/classes -name '*.class')
(cd build/dex && zip -q -j ../unsigned.apk classes.dex)
"$BT/zipalign" -f -p 4 build/unsigned.apk build/aligned.apk
if [ ! -f "$KS" ]; then
  mkdir -p "$KEYDIR" && chmod 700 "$KEYDIR"
  ( umask 077; head -c 24 /dev/urandom | base64 | tr -d '/+=' > "$KP" )
  keytool -genkeypair -keystore "$KS" -storepass "$(cat "$KP")" -keypass "$(cat "$KP")" -alias alarmsound \
    -keyalg RSA -keysize 3072 -validity 36500 -dname "CN=AlarmSound" >/dev/null 2>&1
  chmod 600 "$KS"
fi
"$BT/apksigner" sign --ks "$KS" --ks-pass "file:$KP" --ks-key-alias alarmsound --out build/AlarmSound.apk build/aligned.apk
"$BT/apksigner" verify build/AlarmSound.apk && ls -la build/AlarmSound.apk
if [ "${1:-}" = install ]; then
  for s in ${ADB_SERIAL:-$(adb devices | awk 'NR>1 && $2=="device"{print $1}')}; do
    m=$(adb -s "$s" shell getprop ro.product.model 2>/dev/null | tr -d '\r')
    case "$m" in *SHIELD*) continue ;; esac
    echo "install -> $s ($m)"; adb -s "$s" install --no-incremental -r build/AlarmSound.apk
    # HyperOS: Security Center resets Autostart a few seconds after every install/update, and
    # without it HA broadcasts can't wake the app. Re-allow it after the reset and verify.
    for i in 1 2 3 4 5 6; do
      sleep 3
      adb -s "$s" shell appops set local.alarmsound 10008 allow 2>/dev/null || true
      sleep 2
      if adb -s "$s" shell appops get local.alarmsound 10008 2>/dev/null | grep -q ": allow"; then
        [ "$i" -ge 2 ] && { echo "autostart allowed"; break; }
      fi
    done
    # Never hibernate ("Pause app activity if unused"), or alerts silently stop after months unused.
    adb -s "$s" shell appops set --uid local.alarmsound AUTO_REVOKE_PERMISSIONS_IF_UNUSED ignore 2>/dev/null || true
    adb -s "$s" shell appops get local.alarmsound 10008 | grep -q ": allow" || echo "WARNING: autostart not allowed; set it in Settings > Apps > Alarm Sound" >&2
  done
fi
