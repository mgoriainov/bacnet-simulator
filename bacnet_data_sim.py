import asyncio
import BAC0
import random
import math
import time

from BAC0.core.devices.local.factory import (analog_input, binary_input, binary_output, multistate_value, 
                                             binary_value, ObjectFactory, analog_output, analog_value)
# Парсинг файла со всеми точками
with open('точки скада.csv', 'r', encoding='cp1251') as f:
    devices_dict = {}
    point_type_dict = {'temp': ('темп.', 'темпер.', 'температур', 'temperature', 'te.', 'tmp'), 'power': ('мощность', 'power'),
                 'current': ('ток', 'current'), 'voltage': ('напряжение',), 'energy': ('энергия',), 'cos': ('cos',),
                 'pressure': ('pressure', 'press', 'давление', 'давл', 'перепад', 'pe.')}
    
    for line in f.read().splitlines()[1:]:
        line_list = line.split(';')
        if all(el for el in line_list):
            point_name, garbage, obj_id, device_id, obj_name  = line_list[2:]
            device_id = device_id.split(':')[1]
            obj_point_type, obj_point_id = obj_id.split(':')
            point_category = 'other'
            for type in point_type_dict:
                if any(i in point_name.lower() for i in point_type_dict[type]):
                    point_category = type
                    break
            devices_dict.setdefault(device_id, []).append((point_name, obj_point_type, obj_point_id, obj_name,
                                                           point_category))

# Парсинг файла с пределами
with open('Пределы для точек скада.csv', 'r', encoding='cp1251') as f:
    limits_dict = {}
    for line in f.read().splitlines()[1:]:
        cat, mn, mx = line.split(';')
        limits_dict[cat.lower()] = (float(mn), float(mx))    

async def main(devices_dict, limits_dict):
    types_dict = {'BI': binary_input, 'AI': analog_input, 'BO': binary_output, 
                      'MSV': multistate_value, 'BV': binary_value, 'AO': analog_output,
                      'AV': analog_value}
    all_devices_list = []
    units_dict = {'temp': 'degreesCelsius', 'power': 'watts', 'current': 'amperes', 'voltage': 'volts', 
                  'energy': 'joules', 'cos': 'noUnits', 'pressure': 'pascals', 'other': 'noUnits'}

    for index, id in enumerate(devices_dict):
        dev = BAC0.lite(deviceId=int(id), ip='172.31.51.79/20', port=47809 + index, localObjName=f"Device {id}")
        while not dev._initialized:
            await asyncio.sleep(0.01)
        for obj in devices_dict[id]:
            point_name, obj_point_type, obj_point_id, obj_name, point_category = obj
            if obj_point_type in ('AI', 'AO', 'AV'):
                last_obj = types_dict[obj_point_type](name=obj_name, instance=int(obj_point_id), description=point_name, 
                                                      properties={"units": units_dict[point_category]})
            else:
                last_obj = types_dict[obj_point_type](name=obj_name, instance=int(obj_point_id), description=point_name)        
        last_obj.add_objects_to_application(dev)

        ObjectFactory.clear_objects()
        all_devices_list.append(dev)     

    try:
        while True:
            for dev, id in zip(all_devices_list, devices_dict):
                for point in devices_dict[id]:
                    if point[1] in ('AI', 'AO', 'AV') and 'уставка' not in point[0]:
                        mn, mx = limits_dict[point[-1]]
                        dev[point[-2]].presentValue = random.uniform(mn, mx)
            await asyncio.sleep(2)
    finally:
        for device in all_devices_list:
            device._disconnect()

asyncio.run(main(devices_dict, limits_dict))