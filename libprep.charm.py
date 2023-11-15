from opentrons import protocol_api
# import opentrons.execute # in jupyter
import time
import json

#protocol = opentrons.execute.get_protocol_api('2.13')
#尽管我在使用2.14 的机器，2.13的api也是可以的。2.14版本之后似乎禁用了直接使用jupyter 调用
#protocol.home()


metadata = {
    'protocolName': 'Automated CHARM library prep protocol',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}

################CHARM library prep configuration################
malbac_product_concentration_columns = [30,40,30,40,30,40,30,40,30,40,30,40]

def run(protocol: protocol_api.ProtocolContext):
    protocol.home()
    # load labwares
    with open('./xinglab_pcr96well_semiskirt_280ul.json') as labware_file:
        labware_def = json.load(labware_file)

        malbac_plate = protocol.load_labware_from_definition(labware_def,location='1')
        reagent_plate = protocol.load_labware_from_definition(labware_def,location='2')
        # def in reagent_plate
        # water, transposition mix, MALBAC products, SDS, PCR mix, i5 index, i7 index
        dilute_plate = protocol.load_labware_from_definition(labware_def,location='3')
        pcr_plate = protocol.load_labware_from_definition(labware_def,location='4')

    with open('./xinglab_axygen_96_diytiprack_10ul.json') as labware_file:
        labware_def = json.load(labware_file)
        tipracks = protocol.load_labware_from_definition(labware_def,location=['4','5','6','7','8','9','10','11','12'])

    # load instrument
    pipette = protocol.load_instrument('p20_multi', 'left', tip_racks=[tipracks])
    # set flow rate for small volume
    pipette.flow_rate.aspirate = 5  
    pipette.flow_rate.dispense = 5
    
    # reagents
    water = reagent_plate.wells_by_name()['1']
    TranspositionMix = reagent_plate.wells_by_name()['2']
    SDS = reagent_plate.wells_by_name()['3']
    PCRMix = reagent_plate.wells_by_name()['4']
    i5index = reagent_plate.wells_by_name()['5']
    i7index = reagent_plate.wells_by_name()['6']
    

    # protocol
    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)

    # input water volumes for malbac products dialution to 5ng/ul, 
    # for example, original concentration is 40 ng/ul, load 2 ul of malbac products and 14 ul of water

    final_concentration = 5
    malbac_product_volume = 2
    water_volume = [malbac_product_volume/final_concentration*concentration-malbac_product_volume for concentration in malbac_product_concentration_columns]

    # transfer water to dilute plate
    pipette.pick_up_tip()
    for i in range(12):
        pipette.aspirate(water_volume[i], water[0].bottom(-1)) 
        pipette.dispense(water_volume[i], dilute_plate.columns_by_name()[str(i+1)][0].bottom())
        