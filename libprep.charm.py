"""
Automated CHARM library prep protocol
@Author: zliu
@Date: 2023-11-05
"""

from opentrons import protocol_api
# import opentrons.execute # in jupyter
import time
import json
import math
import os

metadata = {
    'protocolName': 'Automated CHARM library prep protocol',
    'author': 'zliu <skelviper@hotmail.com>',
    'apiLevel': '2.13' 
}

################CHARM library prep configuration################
malbac_product_concentration_columns = [30,30,30,30,30,30,30,30,30,30,30,30]
folder_path = './'
################End CHARM library prep configuration################

def run(protocol: protocol_api.ProtocolContext):
    if not protocol.rail_lights_on:
        protocol.set_rail_lights(True)
    protocol.home()

    tip_track = True
    
    # load labwares
    with open('./xinglab_pcr96well_semiskirt_280ul.json') as labware_file:
        labware_def = json.load(labware_file)

        malbac_plate = protocol.load_labware_from_definition(labware_def,location='6')
        reagent_plate = protocol.load_labware_from_definition(labware_def,location='9')
        dilute_plate = protocol.load_labware_from_definition(labware_def,location='3')
        pcr_plate = protocol.load_labware_from_definition(labware_def,location='2')
        enrich_plate = protocol.load_labware_from_definition(labware_def,location='5')
        #i5_plate = protocol.load_labware_from_definition(labware_def,location='4')
        #i7_plate = protocol.load_labware_from_definition(labware_def,location='1')

    with open('./xinglab_axygen_96_diytiprack_10ul.json') as labware_file:
        labware_def = json.load(labware_file)
        tipracks = protocol.load_labware_from_definition(labware_def,location=['1','4','7','8','10','11'])

    # load instrument
    pipette = protocol.load_instrument('p20_multi', 'left', tip_racks=[tipracks])

    tip_log = {val: {} for val in protocol.loaded_instruments.values()}
    tip_file_path = folder_path + '/tip_log.json'
    if tip_track and not protocol.is_simulating():
        if os.path.isfile(tip_file_path):
            with open(tip_file_path) as json_file:
                data = json.load(json_file)
                for pipette in tip_log:
                    if pipette.name in data:
                        tip_log[pipette]['count'] = data[pipette.name]
                    else:
                        tip_log[pipette]['count'] = 0
        else:
            for pipette in tip_log:
                tip_log[pipette]['count'] = 0
    else:
        for pipette in tip_log:
            tip_log[pipette]['count'] = 0

    for pipette in tip_log:
        if pipette.type == 'multi':
            tip_log[pipette]['tips'] = [tip for rack in pipette.tip_racks
                                    for tip in rack.rows()[0]]
        else:
            tip_log[pipette]['tips'] = [tip for rack in pipette.tip_racks
                                    for tip in rack.wells()]
        tip_log[pipette]['max'] = len(tip_log[pipette]['tips'])

    def _pick_up(pipette, loc=None):
        if tip_log[pipette]['count'] == tip_log[pipette]['max'] and not loc:
            protocol.pause('Replace ' + str(pipette.max_volume) + 'µl tipracks before \
resuming.')
            pipette.reset_tipracks()
            tip_log[pipette]['count'] = 0
        if loc:
            pipette.pick_up_tip(loc)
        else:
            pipette.pick_up_tip(tip_log[pipette]['tips'][tip_log[pipette]['count']])
            tip_log[pipette]['count'] += 1

    # set flow rate for small volume
    pipette.flow_rate.aspirate = 5  
    pipette.flow_rate.dispense = 5
    
    # def in reagent_plate
    # water, transposition mix, SDS, PCR mix, enriched PCR mix
    water = reagent_plate.wells_by_name()['1']
    TranspositionMix = reagent_plate.wells_by_name()['2']
    SDS = reagent_plate.wells_by_name()['3']
    PCRMix = reagent_plate.wells_by_name()['4']
    enrich_PCRMix = reagent_plate.wells_by_name()['5']

    # input water volumes for malbac products dialution to 5ng/ul, 
    # for example, original concentration is 40 ng/ul, load 2 ul of malbac products and 14 ul of water

    final_concentration = 5
    malbac_product_volume = 2
    water_volume = [malbac_product_volume/final_concentration*concentration-malbac_product_volume for concentration in malbac_product_concentration_columns]

    # transfer water to dilute plate
    _pick_up(pipette)
    for i in range(12):
        pipette.aspirate(water_volume[i], water[0].bottom()) 
        pipette.dispense(water_volume[i], dilute_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.move_to(dilute_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
    pipette.drop_tip()

    # transfer TranspositionMix to pcr plate
    TranspositionMix_volume = 6
    _pick_up(pipette)
    for i in range(12):
        pipette.aspirate(TranspositionMix_volume, TranspositionMix[0].bottom())
        pipette.dispense(TranspositionMix_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.move_to(pcr_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
    pipette.drop_tip()

    # transfer malbac products to dilute plate, mix, and transfer to pcr plate
    for i in range(12):
        _pick_up(pipette)
        pipette.aspirate(malbac_product_volume, malbac_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.dispense(malbac_product_volume, dilute_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.mix(10, 16,rate=10)
        pipette.aspirate(malbac_product_volume*2, dilute_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.dispense(malbac_product_volume*2, pcr_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.mix(10,8,rate=10)
        pipette.move_to(pcr_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
        pipette.drop_tip()

    # Pause for Tn5 reaction
    protocol.pause('Pause and transfer PCR plate to thermocycler for Tn5 reaction')

    # transfer SDS to pcr plate and split the library into two plates(Hi-C & Enrich)
    SDS_volume = 2.5
    half_lib_volume = 6.25

    for i in range(12):
        _pick_up(pipette)
        pipette.aspirate(SDS_volume, SDS[0].bottom())
        pipette.dispense(SDS_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.mix(10, 10,rate=10)
        pipette.aspirate(half_lib_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.dispense(half_lib_volume, enrich_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.move_to(enrich_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
        pipette.drop_tip()
    
    # replace 3 and 6 with i5/i7 index , while SDS reaction
    protocol.comment('Please replace 3 and 6 with i5/i7 index, while SDS reaction')
    for _ in range(6):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=1)
    # incubate at RT for 10 min
    protocol.delay(minutes=9, seconds=54)

    del protocol.deck['3']
    del protocol.deck['6']
    with open('./xinglab_pcr96well_semiskirt_280ul.json') as labware_file:
        labware_def = json.load(labware_file)
        i5_plate = protocol.load_labware_from_definition(labware_def,location='6')
        i7_plate = protocol.load_labware_from_definition(labware_def,location='3')

    # transfer i5 index to pcr plate,
    # split pcr plate into two plates, one for Hi-C library, one for MALBAC library
    # for Hi-C library
    i5_volume = 2
    i7_volume = 2
    for i in range(12):
        _pick_up(pipette)
        pipette.aspirate(i5_volume, i5_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.dispense(i5_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom())
        #pipette.mix(10, 6,rate=10)
        pipette.move_to(pcr_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
        pipette.drop_tip()
    for i in range(12):
        _pick_up(pipette)
        pipette.aspirate(i7_volume, i7_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.dispense(i7_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom())
        #pipette.mix(10, 8,rate=10)
        pipette.move_to(pcr_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
        pipette.drop_tip()

    # transfer PCR mix to pcr plate
    PCRMix_volume = 9.75
    for i in range(12):
        _pick_up(pipette)
        pipette.aspirate(PCRMix_volume, PCRMix[0].bottom())
        pipette.dispense(PCRMix_volume, pcr_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.mix(10, 15,rate=10)
        pipette.move_to(pcr_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
        pipette.drop_tip()

    # Pause for library amplification
    for _ in range(6):
        protocol.set_rail_lights(not protocol.rail_lights_on)
        protocol.delay(seconds=1)
    protocol.pause('Pause. 1. Transfer PCR plate to thermocycler for library amplification. 2. replace i5/i7 index for enrich lib.')

    # transfer enriched PCR mix to enrich plate
    enrich_PCRMix_volume = 11.75
    for i in range(12):
        _pick_up(pipette)
        pipette.aspirate(enrich_PCRMix_volume, enrich_PCRMix[0].bottom())
        pipette.dispense(enrich_PCRMix_volume, enrich_plate.columns_by_name()[str(i+1)][0].bottom())
        #pipette.mix(10, 12,rate=10)
        pipette.move_to(enrich_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
        pipette.drop_tip()

    # transfer i5 index to enrich plate
    i5_volume = 2
    for i in range(12):
        _pick_up(pipette)
        pipette.aspirate(i5_volume, i5_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.dispense(i5_volume, enrich_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.mix(10, 15,rate=10)
        pipette.move_to(enrich_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
        pipette.drop_tip()

    # Pause for library amplification
    protocol.pause('Pause and transfer enrich plate to thermocycler for library amplification')

    # trnasfer i7 index to enrich plate
    i7_volume = 2
    for i in range(12):
        _pick_up(pipette)
        pipette.aspirate(i7_volume, i7_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.dispense(i7_volume, enrich_plate.columns_by_name()[str(i+1)][0].bottom())
        pipette.mix(10, 15,rate=10)
        pipette.move_to(enrich_plate.columns_by_name()[str(i+1)][0].bottom(20))
        pipette.blow_out()
        pipette.drop_tip()
    
    # Pause for library amplification
    protocol.pause('Pause and transfer enrich plate to thermocycler for library amplification')
    
    # track final used tip
    if tip_track and not protocol.is_simulating():
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        data = {pipette.name: tip_log[pipette]['count'] for pipette in tip_log}
        with open(tip_file_path, 'w') as outfile:
            json.dump(data, outfile)

    protocol.comment('Protocol complete!')
    