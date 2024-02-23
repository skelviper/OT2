"""
track liquid level in 96 well plate
@Author: zliu
@Version: 0.1
@Date: 2023-12-10
"""

from opentrons import protocol_api
import subprocess
import time
import math

# define constant
AUDIO_FILE_PATH = '/var/lib/jupyter/notebooks/reminder_tone.mp3' 

# define custom functions
def run_quiet_process(command): 
    subprocess.check_output('{} &> /dev/null'.format(command), shell=True) 

def speaker(): 
    """
    play reminder tone
    """
    print('Speaker') 
    print('Next\t--> CTRL-C')
    try:
        run_quiet_process('mpg123 {}'.format(AUDIO_FILE_PATH))
    except KeyboardInterrupt:
        print("cancel")

def _calc_height(volume, diameter=5.5, bottom_offset=0.3):
    """
    calculate liquid height in well.
    Assume well is a cylinder + cone, Vcone = 71.53 mm^3
    This is a rough approximation.
    """
    height_cone = 0
    height_cylinder = 0

    #if volume <= 100:
    #    height_cone = volume / (math.pi * (diameter / 2) ** 2) * 3 
    #else:
    #    volume -= 100
    height_cylinder = volume / (math.pi * (diameter / 2) ** 2)

    #height = height_cone + height_cylinder
    height = height_cylinder
    if height < 0:
        return 0 + bottom_offset
    else:
        return height + bottom_offset

metadata = {
    'protocolName': 'liquid level simple track',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}

def run(protocol: protocol_api.ProtocolContext):

    def _pick_up(pipette):
        """
        pick up tip, if no tip available, pause and wait for tip replacement
        """
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            for _ in range(8):
                protocol.set_rail_lights(not protocol.rail_lights_on)
                if protocol.rail_lights_on:
                    speaker()
                protocol.delay(seconds=0.2)
            protocol.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()

    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)
    protocol.home()

    plate = protocol.load_labware('pcr96well_nonskirt_280ul', location = '2')
    reagent = protocol.load_labware('xinglab_8stripetube',location='9')

    tiprack = protocol.load_labware('axygen_96_diytiprack_10ul', location = '10')

    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack])

    pipette.flow_rate.aspirate = 5
    pipette.flow_rate.dispense = 5

    bottom_offset = 0.3

    water = reagent.wells_by_name()['A1']

    #move_volume = 2.5
    col_num = 12

    # for i in range(col_num):
    #     _pick_up(pipette)

    #     pipette.aspirate(move_volume, water.bottom(_calc_height(volume = (col_num - i - 1)*move_volume, bottom_offset=bottom_offset)))
    #     pipette.dispense(move_volume, plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))

    #     pipette.return_tip()

    # protocol.pause('Check Volume')

    move_volume = 10
    for i in range(col_num):
        _pick_up(pipette)

        pipette.aspirate(move_volume, water.bottom(_calc_height(volume = (col_num - i - 1)*move_volume, bottom_offset=bottom_offset)))
        pipette.dispense(move_volume, plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))

        pipette.mix(5, 5, plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset+1),rate=20)

        pipette.drop_tip()

    protocol.pause('Check Volume')

    # move_volume = 12.5
    # for i in range(col_num):
    #     _pick_up(pipette)

    #     pipette.aspirate(move_volume, plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
    #     pipette.dispense(move_volume, water.bottom(_calc_height(volume = i*move_volume, bottom_offset=bottom_offset)))

    #     pipette.return_tip()
    


    protocol.comment('Protocol complete!')

