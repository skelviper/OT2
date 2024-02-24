"""
Automated CHARM library prep protocol
@Author: zliu
@Version: 2.0
@Date: 2024-2-23
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
    #height_cone = 0
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
    'protocolName': 'CHARM library prep: 2.SDS',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}

################CHARM library prep configuration################
malbac_product_concentration_columns = [25 for i in range(12)]
if_test_run = False
bottom_offset = 0.3
################End CHARM library prep configuration################

if if_test_run:
    col_num = 3
else:
    col_num = 12

def run(protocol: protocol_api.ProtocolContext):
    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)
    protocol.home()

    # protocol.max_speeds['X'] = 500
    # protocol.max_speeds['Y'] = 500

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

    reagent_plate = protocol.load_labware('xinglab_8stripetube',location='9')
    pcr_plate = protocol.load_labware('xinglab_pcr96well_semiskirt_280ul',location='2')
    enrich_plate = protocol.load_labware('xinglab_pcr96well_semiskirt_280ul',location='5')
    tipracks = [protocol.load_labware('axygen_96_diytiprack_10ul',location=s) for s in ['1']]

    # load instrument
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tipracks)

    # set flow rate for small volume
    pipette.flow_rate.aspirate = 5  
    pipette.flow_rate.dispense = 5
    
    # def in reagent_plate
    # water, transposition mix, SDS, PCR mix, enriched PCR mix

    SDS = reagent_plate.wells_by_name()['A3']

    # transfer SDS to pcr plate and split the library into two plates(Hi-C & Enrich)
    SDS_volume = 2.5
    half_lib_volume = 6.25

    for i in range(col_num):
        _pick_up(pipette)
        pipette.aspirate(SDS_volume, SDS.bottom(_calc_height((col_num - i - 1)*SDS_volume)))
        pipette.dispense(SDS_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        pipette.mix(5, 10,rate=20, location = pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset+1))
        pipette.aspirate(half_lib_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        pipette.dispense(half_lib_volume, enrich_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        if i != col_num-1:
            pipette.drop_tip(home_after=False)
        else:
            pipette.drop_tip()
    
    # replace 3 and 6 with i5/i7 index , while SDS reaction
    for _ in range(8):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        if protocol.rail_lights_on:
            speaker()
        protocol.delay(seconds=0.2)
    protocol.comment('Please replace 3 and 6 with i5/i7 index, while SDS reaction (Set timer manually for 10 min)')
    
