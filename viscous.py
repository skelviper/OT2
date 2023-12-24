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
                pipette.pick_up_tip(presses=2)
            else:
                pipette.pick_up_tip(presses=2, location=location)
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

    plate = protocol.load_labware('pcr96well_nonskirt_280ul', location = '2')
    tiprack = protocol.load_labware('axygen_96_diytiprack_10ul', location = '8')

    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack])

    pipette.flow_rate.aspirate = 5
    pipette.flow_rate.dispense = 5

    bottom_offset = 0.5

    water = plate.wells_by_name()['A1']

    _pick_up(pipette,location=tiprack.wells_by_name()['A4'])

    for i in range(11):
        pipette.aspirate(10, water.bottom(bottom_offset))
        #pipette.move_to(water.top(20))
        #time.sleep(2)
        pipette.dispense(10, plate.columns_by_name()[str(i+2)][0].bottom(bottom_offset))
        #pipette.move_to(plate.columns_by_name()[str(i+2)][0].top(20))
        #time.sleep(2)

    protocol.pause("")

    for i in range(11):
        pipette.aspirate(10, plate.columns_by_name()[str(i+2)][0].bottom(bottom_offset))
        #pipette.move_to(water.top(20))
        #time.sleep(2)
        pipette.dispense(10, water.bottom(bottom_offset))


    protocol.comment('Protocol complete!')

