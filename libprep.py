from opentrons import protocol_api

metadata = {
    'protocolName': 'Single cell library prep protocol for PKU',
    'author': 'FAE <fae@opentrons.com>',
    'source': 'Peking University',
    'apiLevel': '2.14'   # CHECK IF YOUR API LEVEL HERE IS UP TO DATE
                         # IN SECTION 5.2 OF THE APIV2 "VERSIONING"
}


def run(ctx: protocol_api.ProtocolContext):

    # load modules
    tc_mod = ctx.load_module(module_name='thermocyclerModuleV2')
    #hs_mod = ctx.load_module(module_name='heaterShakerModuleV1',location="1")
    # load labware
    tc_plate = tc_mod.load_labware(name='armadillo_96_wellplate_200ul_pcr_full_skirt')
    #reagent_plate = hs_mod.load_labware(name='opentrons_96_pcr_adapter_armadillo_wellplate_200ul')
    reagent_plate = ctx.load_labware('armadillo_96_wellplate_200ul_pcr_full_skirt','4')
    index_plate = ctx.load_labware('armadillo_96_wellplate_200ul_pcr_full_skirt','1')
    # load tipracks
    tipracks_20 = [ctx.load_labware('opentrons_96_tiprack_20ul', s) for s in ['2','3','5','6','9']]
    
    # load instrument
    m20 = ctx.load_instrument('p20_multi_gen2','right',tip_racks=tipracks_20)
    # pipette functions   # INCLUDE ANY BINDING TO CLASS
    '''
    def pick_up(pipette):
        try:
            pipette.pick_up_tip()
        except protocol_api.labware.OutOfTipsError:
            ctx.pause("Replace empty tip racks")
            pipette.reset_tipracks()
            pipette.pick_up_tip()
    '''
    


    # helper functions


    # reagents
    TranspositionMix = reagent_plate.wells_by_name()['A1']
    MALBACProducts = reagent_plate.wells_by_name()['A2']
    SDS = reagent_plate.wells_by_name()['A3']
    PCRMix = reagent_plate.wells_by_name()['A4']
    Index = index_plate.wells()

    # plate, tube rack maps

    # protocol
    if not ctx.rail_lights_on:
        ctx.set_rail_lights(True)

    tc_mod.open_lid()
    #hs_mod.close_labware_latch()

    # Transfer 3ul Transposition Mix to sample plate on Thermocycler
    m20.transfer(
        volume = 3,
        source = TranspositionMix,
        dest = tc_plate.wells(),
        new_tip = "always",
        mix_after = (3, 5),
        blow_out=True,  # required to set location
        blowout_location="destination well",
    )

    # Transfer 2ul MALBAC products to sample plate on Thermocycler
    m20.transfer(
        volume = 2,
        source = MALBACProducts,
        dest = tc_plate.wells(),
        new_tip = "always",
        mix_after = (5, 7),
        blow_out=True,  # required to set location
        blowout_location="destination well",
    )

    # 55C Incubate for 10min

    tc_mod.close_lid()
    tc_mod.set_lid_temperature(temperature=65)
    tc_mod.set_block_temperature(
        temperature=55,
        hold_time_minutes=10,
        block_max_volume=10
    )
    tc_mod.set_block_temperature(
        temperature=4,
        hold_time_seconds=30,
        block_max_volume=10
    )
    tc_mod.deactivate_lid()
    tc_mod.deactivate_block()
    tc_mod.open_lid()

    # Transfer 2ul SDS  to sample plate on Thermocycler
    m20.transfer(
        volume = 1.3,
        source = SDS,
        dest = tc_plate.wells(),
        new_tip = "always",
        mix_after = (5, 8),
        blow_out=True,  # required to set location
        blowout_location="destination well",
    )

    # Incubate 10min at room temperature
    ctx.delay(minutes=10)

    # Transfer 2ul i5  to sample plate on Thermocycler
    m20.transfer(
        volume = 2,
        source = Index,
        dest = tc_plate.wells(),
        new_tip = "always",
        blow_out=True,  # required to set location
        blowout_location="destination well",
    )

    #Transfer 11.7ul PCRMix to sample plate on Thermocycler
    m20.transfer(
        volume = 11.7,
        source = PCRMix,
        dest = tc_plate.wells(),
        new_tip = "always",
        mix_after = (5, 16),
        blow_out=True,  # required to set location
        blowout_location="destination well",
    )

    tc_mod.close_lid()
    tc_mod.set_lid_temperature(temperature=105)

    tc_mod.set_block_temperature(
        temperature=72,
        hold_time_minutes=3,
        block_max_volume=20
    )
    tc_mod.set_block_temperature(
        temperature=98,
        hold_time_seconds=30,
        block_max_volume=20
    )
    profile = [
        {'temperature':98, 'hold_time_seconds':15},
        {'temperature':60, 'hold_time_seconds':30},
        {'temperature':72, 'hold_time_minutes':2}
    ]
    tc_mod.execute_profile(steps=profile, repetitions=5, block_max_volume=20)
    tc_mod.set_block_temperature(
        temperature=4,
        hold_time_seconds=30,
        block_max_volume=20
    )
    tc_mod.open_lid()
    

    ctx.pause("Replace empty tip racks")
    m20.reset_tipracks()

    # Transfer 2ul i5  to sample plate on Thermocycler
    m20.transfer(
        volume = 2,
        source = Index,
        dest = tc_plate.wells(),
        new_tip = "always",
        mix_after = (5, 20),
        blow_out=True,  # required to set location
        blowout_location="destination well",
    )

    tc_mod.close_lid()
    profile = [
        {'temperature':98, 'hold_time_seconds':30},
        {'temperature':60, 'hold_time_seconds':30},
        {'temperature':72, 'hold_time_minutes':2}
    ]
    tc_mod.execute_profile(steps=profile, repetitions=5, block_max_volume=22)

    tc_mod.set_block_temperature(
        temperature=72,
        hold_time_minutes=5,
        block_max_volume=22
    )

    tc_mod.set_block_temperature(
        temperature=4,
        hold_time_seconds=30,
        block_max_volume=22
    )

    tc_mod.open_lid()
    
    ctx.pause("Run Completed, Please take the final product to next step, then click resume button!")
    tc_mod.close_lid()
    tc_mod.deactivate_lid()
    tc_mod.deactivate_block()
