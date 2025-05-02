#!/usr/bin/env python3
import ijson
import json
import os

def process_cam_json_to_array(input_path: str, output_path: str):
    """
    读取 input_path（普通 JSON 数组格式），流式提取：
      - timestamp （毫秒）
      - stationID
      - latitude (°)
      - longitude (°)
      - stationType
      - speed_m_s (m/s)
    并按标准 JSON 数组写入 output_path。
    """
    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:

        # 写入数组开头
        fout.write('[\n')
        first = True

        # ijson.items(fin, 'item') 用来逐条读取顶层数组中的元素
        for rec in ijson.items(fin, 'item'):
            # --- 提取并换算 ---
            ts = rec.get('timestamp')

            hdr = rec.get('msg', {}).get('header', {})
            station_id = hdr.get('stationID')

            bc = rec.get('msg', {}) \
                    .get('cam', {}) \
                    .get('camParameters', {}) \
                    .get('basicContainer', {})
            hf = rec.get('msg', {}) \
                    .get('cam', {}) \
                    .get('camParameters', {}) \
                    .get('highFrequencyContainer', {}) \
                    .get('basicVehicleContainerHighFrequency', {})

            lat_raw      = bc.get('referencePosition', {}).get('latitude')
            lon_raw      = bc.get('referencePosition', {}).get('longitude')
            station_type = bc.get('stationType')
            speed_raw    = hf.get('speed', {}).get('speedValue')

            latitude  = lat_raw  / 1e7 if lat_raw  is not None else None
            longitude = lon_raw  / 1e7 if lon_raw  is not None else None
            speed_m_s  = speed_raw /   100 if speed_raw is not None else None

            out = {
                'timestamp'   : ts,
                'stationID'   : station_id,
                'latitude'    : latitude,
                'longitude'   : longitude,
                'stationType' : station_type,
                'speed_m_s'   : speed_m_s
            }

            if not first:
                fout.write(',\n')
            fout.write(json.dumps(out, ensure_ascii=False))
            first = False

        # 写入数组结尾
        fout.write('\n]\n')

    print(f"✅ 处理完成，输出文件：{output_path}")

if __name__ == '__main__':
    INPUT_FILE  = 'Data/cams_04_07_7-8/cams_04_07_7-8_3.json'
    OUTPUT_FILE = 'Data/cams_04_07_7-8/cams_04_07_7-8_3_filtered.json'

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"找不到输入文件: {INPUT_FILE}")
    process_cam_json_to_array(INPUT_FILE, OUTPUT_FILE)
