"""
NCsep.py
@Author: zliu
@Version: 0.2
@Date: 2023-12-11
"""

from opentrons import protocol_api
# import opentrons.execute # in jupyter
import time
import json
import math
import os
import subprocess

metadata = {
    'protocolName': 'Nuclear_cytoplasmic separation test',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}

################ configuration ################
if_dry_run = False
################End configuration############

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

def run(protocol: protocol_api.ProtocolContext):
    
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

    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)
    protocol.home()

    # load instrument
    tipracks = [protocol.load_labware('axygen_96_diytiprack_10ul',location=s) for s in ['1']]
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tipracks)

    tubes = protocol.load_labware('xinglab_8stripetube',location='2')
    tubes.set_offset(x=0.00, y=0.00, z=0.00)

    pipette.flow_rate.aspirate = 1
    pipette.flow_rate.dispense = 5

    i = 1
    _pick_up(pipette)
    bottom_offset = 1
    protocol.max_speeds['Z'] = 20
    pipette.aspirate(5, tubes.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
    protocol.max_speeds['Z'] = 100
    pipette.dispense(5, tubes.columns_by_name()[str(i+2)][0].bottom(bottom_offset))
    pipette.drop_tip()

    protocol.comment('Protocol complete!')
    