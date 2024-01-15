"""
Automated CHARM library prep protocol
@Author: zliu
@Version: 0.2
@Date: 2023-11-15
"""

from opentrons import protocol_api
# import opentrons.execute # in jupyter
import time
import json
import math
import os
import subprocess

AUDIO_FILE_PATH = '/var/lib/jupyter/notebooks/reminder_tone.mp3' 
# custom functions

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
    'protocolName': 'Pooling 96 to 8',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}


bottom_offset = 0.3

if if_test_run:
    col_num = 3
else:
    col_num = 12

def run(protocol: protocol_api.ProtocolContext):
    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)
    protocol.home()
    
    def _pick_up(pipette):
        """
        pick up tip, if no tip available, pause and wait for tip replacement
        """
        try:
            pipette.pick_up_tip(presses=2,increment=1)
        except protocol_api.labware.OutOfTipsError:
            for _ in range(8):
                protocol.set_rail_lights(not protocol.rail_lights_on)
                if protocol.rail_lights_on:
                    speaker()
                protocol.delay(seconds=0.2)
            protocol.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip(presses=2,increment=1)

    tube_plate = protocol.load_labware('xinglab_8stripetube',location='3')
    pcr_plate = protocol.load_labware('pcr96well_nonskirt_280ul',location='2')

    tipracks = [protocol.load_labware('axygen_96_diytiprack_10ul',location=s) for s in ['1','4']]

    # load instrument
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tipracks)

    # set flow rate for small volume
    pipette.flow_rate.aspirate = 5  
    pipette.flow_rate.dispense = 5

    # trnasfer lib to enrich 8 stripe tube
    _pick_up(pipette)
    lib_volume = 2
    for i in range(col_num):
        pipette.aspirate(lib_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        pipette.dispense(lib_volume, tube_plate.columns_by_name()['1'][0].bottom(bottom_offset))
        #pipette.drop_tip()
    pipette.drop_tip()

    for _ in range(4):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        if protocol.rail_lights_on:
            speaker()
        protocol.delay(seconds=0.2)

    protocol.comment('Protocol complete!')
    