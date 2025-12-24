def build_segments(episode, is_first: bool, is_last: bool):
    skips = episode.skips or {}

    cuts = []

    for c in skips.get("cuts", []):
        cuts.append(c)
        
    cut_ranges = sorted(
        [
            (
                episode.hms_to_seconds(c["start"]),
                episode.hms_to_seconds(c["end"]),
            )
            for c in cuts
        ]
    )

    segments = []
    cursor = 0.0

    # monta segmentos ignorando cortes
    for start, end in cut_ranges:
        if cursor < start:
            segments.append((cursor, start))
        cursor = max(cursor, end)

    if cursor < episode.duration:
        segments.append((cursor, episode.duration))

    # aplica limites de intro / finish
    start_cut, end_cut = episode.get_cut_times(is_first, is_last)

    final_segments = []
    for s, e in segments:
        s_new = max(s, start_cut)
        e_new = min(e, end_cut)
        if s_new < e_new:
            final_segments.append((s_new, e_new))

    return final_segments


def resolve_offset(segments, offset):
    acc = 0.0
    for start, end in segments:
        seg_len = end - start
        if offset < acc + seg_len:
            return start + (offset - acc)
        acc += seg_len
    return None


def effective_duration(segments):
    return sum(end - start for start, end in segments)
