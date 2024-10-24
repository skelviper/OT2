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
    'protocolName': 'CHARM library prep: 3.Hi-C',
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
    tipracks = [protocol.load_labware('axygen_96_diytiprack_10ul',location=s) for s in ['1','4','7','8','10','11']]

    # load instrument
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tipracks)

    # set flow rate for small volume
    pipette.flow_rate.aspirate = 5  
    pipette.flow_rate.dispense = 5
    
    # def in reagent_plate
    # water, transposition mix, SDS, PCR mix, enriched PCR mix
    PCRMix = reagent_plate.wells_by_name()['A4']

    i5_plate = protocol.load_labware('xinglab_pcr96well_semiskirt_280ul',location='6')

    # transfer i5 index to pcr plate,
    # split pcr plate into two plates, one for Hi-C library, one for MALBAC library
    # for Hi-C library
    i5_volume = 2
    for i in range(col_num):
        _pick_up(pipette)
        pipette.aspirate(i5_volume, i5_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        pipette.dispense(i5_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        if i != col_num-1:
            pipette.drop_tip(home_after=False)
        else:
            pipette.drop_tip()

    # transfer PCR mix to pcr plate
    PCRMix_volume = 11.75
    for i in range(col_num):
        _pick_up(pipette)
        pipette.aspirate(PCRMix_volume, PCRMix.bottom(_calc_height((col_num - i - 1)*PCRMix_volume)))
        pipette.dispense(PCRMix_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        if i != col_num-1:
            pipette.drop_tip(home_after=False)
        else:
            pipette.drop_tip()

    # Pause for library amplification
    for _ in range(8):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        if protocol.rail_lights_on:
            speaker()
        protocol.delay(seconds=0.2)
    protocol.pause('Pause. 1. Transfer PCR plate to thermocycler for library amplification. 2. replace i5/i7 index for enrich lib.')