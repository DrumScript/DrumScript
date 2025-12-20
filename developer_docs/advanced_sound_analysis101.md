2. Spectral Centroid = "Brightness" or "Center of Gravity"
This is the tricky one that is causing your tests to fail.

Imagine the full range of sound (Frequency Spectrum) is a long seesaw or balance beam.

Left side: Low bass frequencies (The "Thud").

Right side: High treble frequencies (The "Hiss", "Click", or "Sizzle").

The Spectral Centroid is the exact point where you would place your finger under the beam to make it balance perfectly.

Low Centroid (< 150 Hz): The seesaw is heavy on the left. The sound is muffled, dark, and deep. Think of a heartbeat or a distant explosion.

High Centroid (> 2000 Hz): The seesaw is heavy on the right. The sound is bright, sharp, or tinny. Think of a whistle or a cymbal.

Why your Kicks are failing
You set the rule to < 150 Hz. This is extremely low. It effectively demands that the kick has zero high frequencies.

However, almost all modern kick drums consist of two parts:

The Thud (50-100 Hz): The body of the sound.

The Click (2000-5000 Hz): The attack of the beater hitting the skin.