"""
Dilution test for viscous liquid 
@Author: zliu
@Version: 0.1
@Date: 2023-12-10
"""

from opentrons import protocol_api
import subprocess
import time

# define constant
AUDIO_FILE_PATH = '/var/lib/jupyter/notebooks/reminder_tone.mp3' 


# define custom functions
def run_quiet_process(command): 
    subprocess.check_output('{} &> /dev/null'.format(command), shell=True) 

def speaker(): 
    print('Speaker') 
    print('Next\t--> CTRL-C')
    try:
        run_quiet_process('mpg123 {}'.format(AUDIO_FILE_PATH))
    except KeyboardInterrupt:
        print("cancel")
    

metadata = {
    'protocolName': 'viscous liquid test for calibration',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}


def run(protocol: protocol_api.ProtocolContext):

    def _pick_up(pipette,location=None):
        try:
            if location is None:
                pipette.pick_up_tip(presses=2,increment=1)
            else:
                pipette.pick_up_tip(presses=2,increment=1, location=location)
        except protocol_api.labware.OutOfTipsError:
            for _ in range(8):
                protocol.set_rail_lights(not protocol.rail_lights_on)
                if protocol.rail_lights_on:
                    speaker()
                protocol.delay(seconds=0.2)
            protocol.pause("Replace empty tip racks")
            pipette.reset_tipracks()
    
    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)
    protocol.home()

    plate = protocol.load_labware('pcr96well_nonskirt_280ul', location = '9')
    reagent = protocol.load_labware('xinglab_8stripetube',location='2')
    tiprack = protocol.load_labware('axygen_96_diytiprack_10ul', location = '8')
    #tiprack =protocol.load_labware('opentrons_96_tiprack_10ul',location = '8')
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack])

    pipette.flow_rate.aspirate = 4
    pipette.flow_rate.dispense = 4

    bottom_offset = 0.3

    water = reagent.wells_by_name()['A1']

    cols_id = ["1","4","6","8"]

    for i in range(4):
        _pick_up(pipette,location = tiprack.columns_by_name()[cols_id[i]][0].top(z=0))
        pipette.aspirate(10, water.bottom(bottom_offset))
        pipette.move_to(water.top(20))
        time.sleep(2)
        pipette.dispense(10, reagent.columns_by_name()[cols_id[i]][0].bottom(bottom_offset))
        pipette.move_to(reagent.columns_by_name()[cols_id[i]][0].top(20))
        time.sleep(2)
        pipette.drop_tip()

    # protocol.pause("")

    # _pick_up(pipette,location = tiprack.columns_by_name()['4'][0].top(z=-2.5))
    # for i in range(4):
    #     pipette.aspirate(6, reagent.columns_by_name()[cols_id[i]][0].bottom(bottom_offset))
    #     pipette.dispense(6, water.bottom(bottom_offset))
    # pipette.drop_tip()
    protocol.comment('Protocol complete!')

