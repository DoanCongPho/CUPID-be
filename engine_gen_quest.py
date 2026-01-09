import json
import math

def haversine(lat1, lon1, lat2, lon2):
    # Tính khoảng cách giữa 2 điểm lat/long (km)
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def parse_time(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m

def format_time(m):
    return f"{m//60:02d}:{m%60:02d}"

def find_common_free_slot(constraints1, constraints2, min_duration=120):
    # Tìm khung giờ rảnh chung >= min_duration phút từ 07:00 đến 22:00
    busy1 = [(parse_time(s), parse_time(e)) for s, e in constraints1]
    busy2 = [(parse_time(s), parse_time(e)) for s, e in constraints2]
    start, end = parse_time("07:00"), parse_time("22:00")
    # Tạo mảng đánh dấu bận
    slots = [0] * (end - start)
    for s, e in busy1 + busy2:
        for i in range(max(s, start), min(e, end)):
            slots[i - start] = 1
    # Tìm đoạn liên tục rảnh đủ dài
    length = 0
    for i in range(len(slots)):
        if slots[i] == 0:
            length += 1
            if length >= min_duration:
                slot_start = i - length + 1 + start
                slot_end = slot_start + min_duration
                return format_time(slot_start), format_time(slot_end)
        else:
            length = 0
    return None, None

def get_top3_places(user1, user2, places):
    # Trả về 3 địa điểm có tổng khoảng cách nhỏ nhất
    res = []
    for p in places:
        d1 = haversine(user1['latitude'], user1['longitude'], p['latitude'], p['longitude'])
        d2 = haversine(user2['latitude'], user2['longitude'], p['latitude'], p['longitude'])
        total = d1 + d2
        res.append((total, p, d1, d2))
    res.sort(key=lambda x: x[0])
    return res[:3]

def xp_reward(total_distance):
    # <=5km: 5, >5km: 10
    return 5 if total_distance <= 5 else 10

def gen_quests_for_matches(matches, user_profiles, tasks, places):
    """
    matches: queryset or list of Match objects
    user_profiles: dict {user_id: UserProfile}
    tasks: dict {user_id: list of (start, end) tuples}
    places: list of dicts from places.json
    Returns: list of dicts with quest info for each match (or None if not possible)
    """
    results = []
    for match in matches:
        u1 = match.user1_id
        u2 = match.user2_id
        p1 = user_profiles.get(u1)
        p2 = user_profiles.get(u2)
        if not p1 or not p2:
            results.append(None)
            continue
        if not (p1.home_latitude and p1.home_longitude and p2.home_latitude and p2.home_longitude):
            results.append(None)
            continue
        user1 = {'latitude': p1.home_latitude, 'longitude': p1.home_longitude}
        user2 = {'latitude': p2.home_latitude, 'longitude': p2.home_longitude}
        c1 = tasks.get(u1, [])
        c2 = tasks.get(u2, [])
        # Nếu 1 trong 2 không có task (rảnh nguyên ngày), coi như constraints rỗng
        if not c1:
            c1 = []
        if not c2:
            c2 = []
        start, end = find_common_free_slot(c1, c2)
        if not start:
            results.append(None)
            continue
        top3 = get_top3_places(user1, user2, places)
        for total, place, d1, d2 in top3:
            activity = None
            if place['type'] == 'Cafe':
                activity = 'Coffee date'
            elif place['type'] == 'Dining':
                activity = 'Dinner date'
            elif place['type'] == 'Park':
                activity = 'Walking date'
            elif place['type'] == 'Shopping':
                activity = 'Shopping date'
            elif place['type'] == 'Cinema':
                activity = 'Movie date'
            else:
                activity = 'Hangout'
            results.append({
                "match": match,
                "location_name": place['name'],
                "activity": activity,
                "quest_date": None,  # to be set in view
                "location_latitude": place['latitude'],
                "location_longitude": place['longitude'],
                "status": None,  # to be set in view
                "xp_reward": xp_reward(total),
                "time_start": start,
                "time_end": end,
            })
    return results

if __name__ == "__main__":
    with open('users.json', encoding='utf-8') as f:
        users = {u['id']: u for u in json.load(f)}
    with open('compatibility.json', encoding='utf-8') as f:
        compatibility = json.load(f)
    with open('constraints.json', encoding='utf-8') as f:
        constraints = json.load(f)
    with open('places.json', encoding='utf-8') as f:
        places = json.load(f)

    results = []

    for pair in compatibility:
        u1 = f"u{pair['male_id']}"
        u2 = f"u{pair['female_id']}"
        if u1 not in users or u2 not in users:
            continue
        c1 = constraints.get(u1, [])
        c2 = constraints.get(u2, [])
        if not c1:
            c1 = []
        if not c2:
            c2 = []
        start, end = find_common_free_slot(c1, c2)
        if not start:
            continue
        top3 = get_top3_places(users[u1], users[u2], places)
        for total, p, d1, d2 in top3:
            results.append({
                "user1": {
                    "id": u1,
                    "name": users[u1]['name'],
                    "hint": users[u1]['appearance']
                },
                "user2": {
                    "id": u2,
                    "name": users[u2]['name'],
                    "hint": users[u2]['appearance']
                },
                "location_latitude": p['latitude'],
                "location_longitude": p['longitude'],
                "place_name": p['name'],
                "time_start": start,
                "time_end": end,
                "xp_reward": xp_reward(total),
                "distance_km": round(total, 2)
            })

    # Group by couple, lấy 3 địa điểm/cặp
    from collections import defaultdict
    final = defaultdict(list)
    for r in results:
        key = (r['user1']['id'], r['user2']['id'])
        final[key].append(r)

    # Xuất kết quả
    for (u1, u2), lst in final.items():
        print(f"\nCặp: {users[u1]['name']} - {users[u2]['name']}")
        for i, r in enumerate(lst):
            print(f"  Địa điểm {i+1}: {r['place_name']} ({r['location_latitude']}, {r['location_longitude']})")
            print(f"    Thời gian: {r['time_start']} - {r['time_end']}")
            print(f"    Hint 1: {r['user1']['hint']}")
            print(f"    Hint 2: {r['user2']['hint']}")
            print(f"    XP: {r['xp_reward']} (Tổng khoảng cách: {r['distance_km']} km)")

    # Nếu muốn lưu ra file JSON:
    with open('cupid_results_new.json', 'w', encoding='utf-8') as f:
        json.dump(list(final.values()), f, ensure_ascii=False, indent=2)