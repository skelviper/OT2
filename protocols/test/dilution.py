"""
Dilution test for calibration
@Author: zliu
@Version: 0.1
@Date: 2023-12-10
"""

from opentrons import protocol_api
import subprocess

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
    'protocolName': 'Dilution test for calibration',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}


def run(protocol: protocol_api.ProtocolContext):

    def _pick_up(pipette):
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
    
    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)
    protocol.home()
    

    # plate col def: water,dna,1.25 dilute to 10, 2.5 dilute to 10

    plate = protocol.load_labware('pcr96well_nonskirt_280ul', location = '2')
    tiprack = protocol.load_labware('axygen_96_diytiprack_10ul', location = '1')

    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=[tiprack])

    pipette.flow_rate.aspirate = 5
    pipette.flow_rate.dispense = 5

    bottom_offset = 0.5

    water = plate.wells_by_name()['A1']
    dna = plate.wells_by_name()['A2']

    _pick_up(pipette)

    pipette.aspirate(8.75, water.bottom(bottom_offset))
    pipette.dispense(8.75, plate.columns_by_name()['3'][0].bottom(bottom_offset))
    pipette.move_to(plate.columns_by_name()['3'][0].bottom(20))
    pipette.blow_out()

    pipette.aspirate(8.75, water.bottom(bottom_offset))
    pipette.dispense(8.75, plate.columns_by_name()['4'][0].bottom(bottom_offset))
    pipette.move_to(plate.columns_by_name()['4'][0].bottom(20))
    pipette.blow_out()

    pipette.drop_tip()

    for _ in range(8):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        if protocol.rail_lights_on:
            speaker()
        protocol.delay(seconds=0.2)
    protocol.pause('Start to add water? Press resume to continue')

    # add DNA to water

    _pick_up(pipette)
    pipette.aspirate(1.25, dna.bottom(bottom_offset))
    pipette.dispense(1.25, plate.columns_by_name()['3'][0].bottom(bottom_offset))
    pipette.mix(10, 7.5,rate=15, location=plate.columns_by_name()['3'][0].bottom(1))
    pipette.move_to(plate.columns_by_name()['3'][0].bottom(20))
    pipette.blow_out()
    pipette.drop_tip()

    _pick_up(pipette)
    pipette.aspirate(1.25, dna.bottom(bottom_offset))
    pipette.dispense(1.25, plate.columns_by_name()['4'][0].bottom(bottom_offset))
    pipette.mix(10, 7.5,rate=15, location=plate.columns_by_name()['4'][0].bottom(1))
    pipette.move_to(plate.columns_by_name()['4'][0].bottom(20))
    pipette.blow_out()
    pipette.drop_tip()



    protocol.comment('Protocol complete!')

