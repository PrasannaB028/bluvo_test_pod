import random

ZONES = [
    "top-left", "top-center", "top-right",
    "bottom-left", "bottom-center", "bottom-right"
]

class ZoneAllocator:
    def __init__(self):
        self.active = []   # [(zone, start, end)]
        self.last_zone = None

    def is_free(self, zone, start, end):
        for z, s, e in self.active:
            if z == zone and not (end <= s or start >= e):
                return False
        return True

    def cleanup(self, current_time):
        self.active = [(z,s,e) for (z,s,e) in self.active if e > current_time]

    def choose(self, start, end, prefer_upper=True):
        self.cleanup(start)

        candidates = ZONES.copy()

        if prefer_upper:
            candidates = [
                "top-left", "top-center", "top-right",
                "bottom-left", "bottom-center", "bottom-right"
            ]

        random.shuffle(candidates)

        for zone in candidates:
            if zone == self.last_zone:
                continue
            if self.is_free(zone, start, end):
                self.active.append((zone, start, end))
                self.last_zone = zone
                return zone

        # fallback (guaranteed)
        zone = candidates[0]
        self.active.append((zone, start, end))
        self.last_zone = zone
        return zone
