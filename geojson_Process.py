#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from shapely.geometry import LineString, Point
from rtree import index

# 1. 读取 roads.geojson，只保留 LineString 道路
print("加载道路 GeoJSON …")
roads_fc = json.load(open('Data/roads.geojson', 'r', encoding='utf-8'))

lines = []  # 存放 (way_id, LineString)
idx   = index.Index()

for feat in roads_fc['features']:
    geom = feat.get('geometry', {})
    if geom.get('type') != 'LineString':
        continue
    coords = geom['coordinates']
    line = LineString(coords)
    way_id = feat['properties'].get('@id') or feat['properties'].get('id')
    if way_id is None:
        continue
    # 使用 lines 当前长度作为 R-tree id
    rid = len(lines)
    lines.append((way_id, line))
    idx.insert(rid, line.bounds)

print(f"共索引 {len(lines)} 条道路 LineString。")

# 2. 加载三份 CAM JSON 数据
print("加载 CAM 数据 …")
cam_files = [
    'Data/cams_04_07_7-8/cams_04_07_7-8_1_filtered.json',
    'Data/cams_04_07_7-8/cams_04_07_7-8_2_filtered.json',
    'Data/cams_04_07_7-8/cams_04_07_7-8_3_filtered.json'
]
cam_points = []
for path in cam_files:
    pts = json.load(open(path, 'r', encoding='utf-8'))
    cam_points.extend(pts)
print(f"共加载 {len(cam_points)} 个轨迹点。")

# 3. 将每个点 snap 到最近道路
print("匹配轨迹点到最近道路 …")
for p in cam_points:
    pt = Point(p['longitude'], p['latitude'])
    best_way = None
    best_dist = float('inf')
    # 用 R-tree 检索最近道路
    for rid in idx.intersection((pt.x, pt.y, pt.x, pt.y)):
        way_id, line = lines[rid]
        d = line.distance(pt)
        if d < best_dist:
            best_dist, best_way = d, way_id
    p['way_id'] = best_way

# 4. 按 stationID + way_id 分组
print("按 stationID + way_id 分组 …")
groups = {}
for p in cam_points:
    key = f"{p['stationID']}__{p['way_id']}"
    groups.setdefault(key, []).append(p)

# 5. 生成聚合路段：一条线 + 平均速度
print("生成聚合路段 …")
segments = []
for pts in groups.values():
    pts.sort(key=lambda x: x['timestamp'])
    coords = [[p['longitude'], p['latitude']] for p in pts]
    avg_speed = sum(p['speed_m_s'] for p in pts) / len(pts)
    segments.append({
        'stationID':  pts[0]['stationID'],
        'stationType':pts[0]['stationType'],
        'way_id':     pts[0]['way_id'],
        'speed':      avg_speed,
        'coordinates':coords,
        'timestamps': [p['timestamp'] for p in pts]
    })

print(f"共生成 {len(segments)} 条聚合路段。")

# 6. 写入小文件 segments.json
out_path = 'Data/segments.json'
print(f"写入 {out_path} …")
with open(out_path, 'w', encoding='utf-8') as fp:
    json.dump(segments, fp, ensure_ascii=False)

print("完成！前端只需加载 Data/segments.json，即可高速渲染。")
