def classify_rudiment_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
    """
    Dedicated classification engine for single beats, paradiddles, and rudiments.
    Uses strict, data-driven physics boundaries and ADSR Transient Gating 
    to guarantee perfect single beats and clean ghost notes.
    """
    from drumscript.notation_generator import constants
    classified_events = []
    
    global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0

    for onset_time in onsets:
        start_sample = int(onset_time * sr)
        
        # 1. TIGHT SLICE PADDING (100ms) 
        duration_short_secs = 0.100 
        end_sample_short = start_sample + int(duration_short_secs * sr)

        if end_sample_short > len(audio_data):
            slice_data = audio_data[start_sample:]
            pad_length = end_sample_short - len(audio_data)
            y_window_short = np.pad(slice_data, (0, pad_length), mode='constant')
        else:
            y_window_short = audio_data[start_sample:end_sample_short]

        if len(y_window_short) == 0:
            continue
            
        slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0

        # 2. NOISE FLOOR GATE (10%)
        if slice_max < global_max * 0.10:
            continue

        # 3. LONG SLICE PADDING (1.5s) (for Tom Decay)
        duration_long_secs = 1.5 
        end_sample_long = start_sample + int(duration_long_secs * sr)

        if end_sample_long > len(audio_data):
            slice_data = audio_data[start_sample:]
            pad_length = end_sample_long - len(audio_data)
            y_window_long = np.pad(slice_data, (0, pad_length), mode='constant')
        else:
            y_window_long = audio_data[start_sample:end_sample_long]

        # Extract the physics DNA
        physics_profile = extract_features(y_window_short, y_window_long, sr)
        p = physics_profile
        instruments = []

        # --- RUDIMENT PHYSICS RULES ---
        # 1. IS IT METAL OR SKIN? (Metals have > 20% energy above 5kHz)
        is_metal = p['hfer_5k'] > 0.20
        
        if is_metal:
            # It's a Cymbal or Hat
            if p['decay'] <= constants.HAT_CLOSED_MAX_DECAY: 
                instruments.append('hi_hat_closed')
            elif p['decay'] <= 0.50: 
                instruments.append('hi_hat_open')
            else:
                # Ride vs Crash (Ride is darker < 6000Hz, Crash is brighter > 6000Hz)
                if p['centroid'] > 6000:
                    instruments.append('crash') 
                else:
                    instruments.append('ride') 
        else:
            # It's a Kick, Snare, or Tom
            is_kick_freq = p['peak_freq'] < 105.0
            is_thump = p['lfer'] > 0.35
            
            # Kick decay is short. Toms ring out.
            if is_kick_freq and is_thump and p['decay'] < 0.45:
                instruments.append('kick')
            elif p['hfer'] > 0.20:
                instruments.append('snare')
            else:
                # Toms have long decay and low hfer, separated by hard freq limits
                if p['peak_freq'] < 90.0:
                    instruments.append('low_tom')
                elif p['peak_freq'] < 115.0:
                    instruments.append('mid_tom')
                else:
                    instruments.append('high_tom')
                    
        if not instruments:
            instruments.append('unknown')
        
        classified_events.append({
            "time_sec": float(onset_time), 
            "instruments": instruments, 
            "debug_features": physics_profile
        })

    # --- TRANSIENT ATTACK GATING (kills wobbles/reverb/shimmer of idiophones) ---
    final_events = []
    last_time = -999.0
    
    for i, ev in enumerate(classified_events):
        time_s = ev["time_sec"]
        
        # Always keep the absolute first stick strike
        if i == 0:
            final_events.append(ev)
            last_time = time_s
            continue
            
        last_insts = final_events[-1]["instruments"]
        is_last_metal = any(inst in ['crash', 'ride', 'hi_hat_open', 'hi_hat_closed'] for inst in last_insts)
        
        # Lockout (Allows 150BPM 16th notes = 100ms)
        lockout = 0.15 if is_last_metal else 0.09
        
        if time_s - last_time < lockout:
            continue
            
        # --- ADSR TRANSIENT CHECK ---
        # Compare 30ms before onset to 50ms after onset.
        # A stick hit explodes in volume. A wobble/reverb just sustains smoothly.
        pre_start = max(0, int((time_s - 0.030) * sr))
        pre_end = int(time_s * sr)
        post_end = min(len(audio_data), int((time_s + 0.050) * sr))
        
        pre_data = audio_data[pre_start:pre_end]
        post_data = audio_data[pre_end:post_end]
        
        pre_vol = np.max(np.abs(pre_data)) if len(pre_data) > 0 else 0.0
        post_vol = np.max(np.abs(post_data)) if len(post_data) > 0 else 0.0
        
        # If the volume didn't jump by at least +25%, it's a fake resonance trigger
        if post_vol < pre_vol * 1.25:
            continue
            
        # --- OVERALL VOLUME GATE ---
        # Metals require 40% volume spike. Skins require 15% (for ghost notes).
        required_vol = global_max * 0.40 if is_last_metal else global_max * 0.15
        
        if post_vol > required_vol:
            final_events.append(ev)
            last_time = time_s

    return final_events