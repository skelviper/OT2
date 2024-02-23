"""
Automated CHARM library prep protocol
@Author: zliu
@Version: 0.1
@Date: 2023-11-15
"""

from opentrons import protocol_api
# import opentrons.execute # in jupyter
import time
import json
import math
import os
import subprocess

AUDIO_FILE_PATH = '/etc/audio/speaker-test.mp3' 
def run_quiet_process(command): 
    subprocess.check_output('{} &> /dev/null'.format(command), shell=True) 
def speaker(): 
    print('Speaker') 
    print('Next\t--> CTRL-C')
    try:
        #run_quiet_process('mpg123 {}'.format(AUDIO_FILE_PATH))
        print("1")
    except KeyboardInterrupt:
        pass
        print()

metadata = {
    'protocolName': 'Automated CHARM library prep protocol',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}

################CHARM library prep configuration################
malbac_product_concentration_columns = [55,55,55,55,55,55,55,55,55,55,55,55]
if_dry_run = True
################End CHARM library prep configuration################

if if_dry_run:
    col_num = 3
else:
    col_num = 12

def run(protocol: protocol_api.ProtocolContext):
    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)
    protocol.home()

    tip_track = True
    
    # load labwares in jupyter 
    # with open('./xinglab_pcr96well_semiskirt_280ul.json') as labware_file:
    #     labware_def = json.load(labware_file)

    #     malbac_plate = protocol.load_labware_from_definition(labware_def,location='6')
    #     reagent_plate = protocol.load_labware_from_definition(labware_def,location='9')
    #     dilute_plate = protocol.load_labware_from_definition(labware_def,location='3')
    #     pcr_plate = protocol.load_labware_from_definition(labware_def,location='2')
    #     enrich_plate = protocol.load_labware_from_definition(labware_def,location='5')
    #     #i5_plate = protocol.load_labware_from_definition(labware_def,location='4')
    #     #i7_plate = protocol.load_labware_from_definition(labware_def,location='1')

    # with open('./xinglab_axygen_96_diytiprack_10ul.json') as labware_file:
    #     labware_def = json.load(labware_file)
    #     tipracks = protocol.load_labware_from_definition(labware_def,location=['1','4','7','8','10','11'])

    malbac_plate = protocol.load_labware('pcr96well_nonskirt_280ul',location='6')
    reagent_plate = protocol.load_labware('pcr96well_nonskirt_280ul',location='9')
    dilute_plate = protocol.load_labware('pcr96well_nonskirt_280ul',location='3')
    pcr_plate = protocol.load_labware('pcr96well_nonskirt_280ul',location='2')
    enrich_plate = protocol.load_labware('pcr96well_nonskirt_280ul',location='5')
    tipracks = [protocol.load_labware('axygen_96_diytiprack_10ul',location=s) for s in ['1','4','7','8','10','11']]

    # load instrument
    pipette = protocol.load_instrument('p20_multi_gen2', 'right', tip_racks=tipracks)

    def _pick_up(pipette):
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            speaker()
            for _ in range(16):
                protocol.set_rail_lights(not protocol.rail_lights_on)
                protocol.delay(seconds=0.4)
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()
    

    # set flow rate for small volume
    pipette.flow_rate.aspirate = 5  
    pipette.flow_rate.dispense = 5
    
    # def in reagent_plate
    # water, transposition mix, SDS, PCR mix, enriched PCR mix
    water = reagent_plate.wells_by_name()['A1']
    TranspositionMix = reagent_plate.wells_by_name()['A2']
    SDS = reagent_plate.wells_by_name()['A3']
    PCRMix = reagent_plate.wells_by_name()['A4']
    enrich_PCRMix = reagent_plate.wells_by_name()['A5']

    # input water volumes for malbac products dialution to 5ng/ul, 
    # for example, original concentration is 40 ng/ul, load 2 ul of malbac products and 14 ul of water

    final_concentration = 5
    malbac_product_volume = 2
    water_volume = [malbac_product_volume/final_concentration*concentration-malbac_product_volume for concentration in malbac_product_concentration_columns]

    # transfer water to dilute plate
    _pick_up(pipette)
    for i in range(col_num):
        #pipette.aspirate(water_volume[i], water.bottom()) 
        #pipette.dispense(water_volume[i], dilute_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.mix(8,16,rate=10,location=pcr_plate.columns_by_name()[str(i+1)][0].bottom(1))
        pipette.move_to(pcr_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
    pipette.drop_tip()


    protocol.comment('Protocol complete!')
    