"""
Automated nextera library prep protocol
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
    'protocolName': 'Automated HiRES library prep protocol',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}

################library prep configuration################
malbac_product_concentration_columns = [35 for i in range(12)]
if_dry_run = False
bottom_offset = 0.3
################End library prep configuration############

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


if if_dry_run:
    col_num = 3
else:
    col_num = 12

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

    malbac_plate = protocol.load_labware('xinglab_pcr96well_semiskirt_280ul',location='6')
    reagent_plate = protocol.load_labware('xinglab_8stripetube',location='9')
    dilute_plate = protocol.load_labware('xinglab_pcr96well_semiskirt_280ul',location='3')
    pcr_plate = protocol.load_labware('xinglab_pcr96well_semiskirt_280ul',location='2')
    tipracks = [protocol.load_labware('axygen_96_diytiprack_10ul',location=s) for s in ['1','4','7','8','10','11']]

    # load instrument
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tipracks)
    
    # def in reagent_plate
    # water, transposition mix, SDS, PCR mix
    water = reagent_plate.wells_by_name()['A1']
    TranspositionMix = reagent_plate.wells_by_name()['A2']
    SDS = reagent_plate.wells_by_name()['A3']
    PCRMix = reagent_plate.wells_by_name()['A4']

    # set flow rate for small volume
    pipette.flow_rate.aspirate = 5  
    pipette.flow_rate.dispense = 5

    # transfer TranspositionMix to pcr plate
    TranspositionMix_volume = 3
    _pick_up(pipette)
    for i in range(col_num):
        pipette.aspirate(TranspositionMix_volume, TranspositionMix.bottom(_calc_height((col_num - i - 1)*TranspositionMix_volume)))
        pipette.dispense(TranspositionMix_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
    pipette.drop_tip()

    # transfer malbac products to dilute plate, mix, and transfer to pcr plate
    malbac_product_volume = 2
    for i in range(col_num):
        _pick_up(pipette)
        pipette.aspirate(malbac_product_volume, malbac_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        pipette.dispense(malbac_product_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        pipette.mix(5,4,rate=20, location = pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset+1))
        if i != col_num-1:
            pipette.drop_tip(home_after=False)
        else:
            pipette.drop_tip()

    # Pause for Tn5 reaction
    for _ in range(4):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        if protocol.rail_lights_on:
            speaker()
        protocol.delay(seconds=0.2)
    protocol.pause('Pause and transfer PCR plate to thermocycler for Tn5 reaction')

    # transfer SDS to pcr plate and split the library into two plates(Hi-C & Enrich)
    SDS_volume = 1.25

    for i in range(col_num):
        _pick_up(pipette)
        pipette.aspirate(SDS_volume, SDS.bottom(_calc_height((col_num - i - 1)*SDS_volume)))
        pipette.dispense(SDS_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        pipette.mix(5, 4,rate=20, location = pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset+1))
        if i != col_num-1:
            pipette.drop_tip(home_after=False)
        else:
            pipette.drop_tip()
    
    # replace 3 and 6 with i5/i7 index , while SDS reaction
    for _ in range(4):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        if protocol.rail_lights_on:
            speaker()
        protocol.delay(seconds=0.2)
    protocol.pause('Please replace 3 and 6 with i5/i7 index, while SDS reaction')
    # incubate at RT for 10 min
    # protocol.delay(minutes=10)

    del protocol.deck['3']
    del protocol.deck['6']
    # with open('./xinglab_pcr96well_semiskirt_280ul.json') as labware_file:
    #     labware_def = json.load(labware_file)
    #     i5_plate = protocol.load_labware_from_definition(labware_def,location='6')
    #     i7_plate = protocol.load_labware_from_definition(labware_def,location='3')
    i5_plate = protocol.load_labware('xinglab_pcr96well_semiskirt_280ul',location='6')
    i7_plate = protocol.load_labware('xinglab_pcr96well_semiskirt_280ul',location='3')

    # transfer i5 index to pcr plate,
    # split pcr plate into two plates, one for Hi-C library, one for MALBAC library
    # for Hi-C library
    i5_volume = 2
    i7_volume = 2

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
    for _ in range(4):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        if protocol.rail_lights_on:
            speaker()
        protocol.delay(seconds=0.2)
    protocol.pause('Pause. Transfer PCR plate to thermocycler for library amplification.')


    for i in range(col_num):
        _pick_up(pipette)
        pipette.aspirate(i7_volume, i7_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        pipette.dispense(i7_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom(bottom_offset))
        if i != col_num-1:
            pipette.drop_tip(home_after=False)
        else:
            pipette.drop_tip()

    # Pause for library amplification
    for _ in range(4):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        if protocol.rail_lights_on:
            speaker()
        protocol.delay(seconds=0.2)
    protocol.pause('Pause. Transfer PCR plate to thermocycler for library amplification.')

    protocol.comment('Protocol complete!')
    