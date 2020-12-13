
from time import sleep
import lifxlan

# Bright red (256, 65536, 65536, 3500)


def main():
    lifx = lifxlan.LifxLAN(1)
    counter = 0
    while True:
        try:
            counter += 1
            devices = lifx.get_multizone_lights()
            if len(devices) > 0:
                break
        except lifxlan.WorkflowException:
            pass
    print(f'Found {len(devices)} device(s). Took {counter} requests to find')

    bulb: lifxlan.Light = devices[0]
    bulb: lifxlan.MultiZoneLight = lifxlan.MultiZoneLight(bulb.mac_addr, bulb.ip_addr, source_id=bulb.source_id)
    print(f'Found device: {bulb.get_label()}')

    print('Getting zones')
    counter = 0
    while True:
        try:
            counter += 1
            all_zones = bulb.get_color_zones()
            break
        except lifxlan.WorkflowException:
            pass
    print(f'Took {counter} tries to get zones')
    all_zones[-1] = all_zones[-2]
    rainbow_zones = []
    colors = [lifxlan.RED, lifxlan.ORANGE, lifxlan.YELLOW, lifxlan.GREEN, lifxlan.BLUE, lifxlan.PURPLE]
    colors = [x for x in colors for _ in range(len(all_zones) // len(colors))]
    for i, (h, s, _, k) in enumerate(all_zones):
        h = colors[i % len(colors)][0]
        rainbow_zones.append((h, s, 50000, k))

    print('Attempting to set colors')
    counter = 0
    while True:
        try:
            counter += 1
            bulb.set_zone_colors(rainbow_zones)
            break
        except lifxlan.WorkflowException:
            pass

    print(f'Took {counter} tries to set zone colors')

    #
    #
    # original_power = bulb.get_power()
    # original_color = bulb.get_color()
    # print(f'Original Light Color: {original_color}')
    # print(f'Original Light Power: {original_power}')
    # bulb.set_power('on')
    #
    # sleep(.2)
    #
    # print('Toggling power')
    # toggle_device_power(bulb, .2)
    # print('Toggling color')
    # toggle_light_color(bulb, .2)
    #
    # print('Reverting to original power and color')
    # bulb.set_color(original_color)
    # sleep(1)
    # bulb.set_power(original_power)



def toggle_device_power(device: lifxlan.Light, interval=.5, num_cycles=3):
    original_power_state = device.get_power()
    device.set_power("off")
    rapid = True if interval < 1 else False
    for i in range(num_cycles):
        device.set_power("on", rapid)
        sleep(interval)
        device.set_power("off", rapid)
        sleep(interval)
    device.set_power(original_power_state)


def toggle_light_color(light: lifxlan.Light, interval=0.5, num_cycles=3):
    original_color = light.get_color()
    rapid = True if interval < 1 else False
    for i in range(num_cycles):
        light.set_color(lifxlan.BLUE, rapid=rapid)
        sleep(interval)
        light.set_color(lifxlan.GREEN, rapid=rapid)
        sleep(interval)
    light.set_color(original_color)


if __name__ == '__main__':
    main()
