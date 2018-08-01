'''
Base code from https://pythonprogramming.net/hard-ai-defeat-starcraft-ii-ai-python-sc2-tutorial/
Modified to add defense logic and optimize offensive logic.
'''

import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, \
 CYBERNETICSCORE, STARGATE, VOIDRAY, FORGE, PHOTONCANNON
import random
from sc2.ids.unit_typeid import UnitTypeId


class SPLGEO(sc2.BotAI):
    def __init__(self):
        self.ITERATIONS_PER_MINUTE = 42
        self.MAX_WORKERS = 120

    async def on_step(self, iteration):
        self.iteration = iteration
        await self.distribute_workers()
        await self.build_nexus()
        await self.build_offensive_force()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.build_defense_building()
        await self.build_defense()
        await self.expand()
        await self.offensive_force_buildings()
        await self.attack()

    async def build_workers(self):
        if (len(self.units(NEXUS)) * 16) > len(self.units(PROBE)) and len(self.units(PROBE)) < self.MAX_WORKERS:
            for nexus in self.units(NEXUS).ready.noqueue:
                if self.can_afford(PROBE):
                    await self.do(nexus.train(PROBE))


    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.first)

    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            if len(self.units(ASSIMILATOR)) < len(self.units(NEXUS)):
                vaspenes = self.state.vespene_geyser.closer_than(15.0, nexus)
                for vaspene in vaspenes:
                    if not self.can_afford(ASSIMILATOR):
                        break
                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists:
                        await self.do(worker.build(ASSIMILATOR, vaspene))

    async def expand(self):
        if self.units(NEXUS).amount < (self.iteration / self.ITERATIONS_PER_MINUTE) and self.can_afford(NEXUS):
            if not self.units(NEXUS).amount > 5:
                await self.expand_now()

    async def build_nexus(self, building=None, max_distance=10, location=None):
        if self.can_afford(NEXUS) and len(self.units(NEXUS)) < 2:
            if not building:
                building = self.townhalls.first.type_id       
                assert isinstance(building, UnitTypeId)
                if not location:
                    location = await self.get_next_expansion()
                    if self.can_afford(NEXUS) and len(self.units(NEXUS)) < 2:
                        await self.build(building, near=location, max_distance=max_distance, random_alternative=False,
                         placement_step=1)
            

    async def build_defense_building(self):
        for nexus in self.units(NEXUS).ready:
            pylon = self.units(PYLON).ready
            if pylon.exists and len(self.units(FORGE)) < 1:
                if self.can_afford(FORGE):
                    nexuses = self.units(NEXUS).ready
                    await self.build(FORGE, near=pylon.closest_to(nexuses.first))
 
            
    async def build_defense(self):
        for nexus in self.units(NEXUS).ready:
            if self.units(PYLON).ready.amount >= 2 and self.can_afford(PHOTONCANNON):
                nexuses = self.units(NEXUS).ready
                if len(self.units(PHOTONCANNON)) < 7:
                    await self.build(PHOTONCANNON, near=nexuses.first)
                    

    async def offensive_force_buildings(self):
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).ready.random

            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)

            elif len(self.units(GATEWAY)) < ((self.iteration / self.ITERATIONS_PER_MINUTE)/2):
                if self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    if len(self.units(GATEWAY)) < 1:
                        await self.build(GATEWAY, near=pylon)

            if self.units(CYBERNETICSCORE).ready.exists:
                if len(self.units(STARGATE)) < ((self.iteration / self.ITERATIONS_PER_MINUTE)):
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
                        if len(self.units(STARGATE)) < (self.units(NEXUS).amount) * 2:
                            await self.build(STARGATE, near=pylon)



    async def build_offensive_force(self):

        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                await self.do(sg.train(VOIDRAY))


    def find_target(self, state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units)
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def attack(self):
        aggressive_units = {VOIDRAY: [7, 2]
                            }


        for UNIT in aggressive_units:
            if self.units(UNIT).amount > aggressive_units[UNIT][0] and self.units(UNIT).amount > aggressive_units[UNIT][1]:
                for s in self.units(UNIT).idle:
                    await self.do(s.attack(self.find_target(self.state)))

            elif self.units(UNIT).amount > aggressive_units[UNIT][1]:
                if len(self.known_enemy_units) > 0:
                    for s in self.units(UNIT).idle:
                        await self.do(s.attack(random.choice(self.known_enemy_units)))


run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, SPLGEO()),
    Computer(Race.Terran, Difficulty.Hard)
    ], realtime=False)