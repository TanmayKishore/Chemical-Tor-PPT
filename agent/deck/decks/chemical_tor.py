"""Chemical Terms of Reference (ToR) Deck Specification for Sector 5(f)."""

from __future__ import annotations

from typing import Tuple

from ...data.registry import Chunk
from ..blocks import BLOCKS
from ..constants import CHEMICAL_TOR_DECK
from ..sections.base import Section
from ..sections.chemical_air import flue_and_process_gas, fugitive_ldar
from ..sections.chemical_legal_land import earlier_clearances, land_breakup, land_documents, undertaking_letterhead
from ..sections.chemical_process import manufacturing_process
from ..sections.chemical_products import product_list, raw_materials
from ..sections.chemical_safety import fire_and_peso, general_safety, hazardous_storage, msihc_undertaking, nearest_fire_station
from ..sections.chemical_waste import hazardous_waste, non_hazardous_waste, wastewater_generation, wastewater_treatability
from ..sections.chemical_water import water_balance_table
from ..sections.closing import prayer, thank_you
from ..sections.location import layout_plan, maps, sensitivity_screening, siting_criteria
from ..sections.monitoring import emp_cost_table
from ..sections.opening import contents, cover
from ..sections.project import key_metrics
from ..sections.regulatory import litigation, nabet, statutory_status, threshold_compliance
from . import DeckSpec

SECTIONS: Tuple[Section, ...] = (
    # Block A: Opening
    Section("cover", "A", 1, "Title / Cover Slide", cover, chunks=(Chunk.BASIC,), structural=True),
    Section("contents", "A", 2, "Presentation Contents", contents, chunks=(), structural=True),
    Section("nabet", "A", 3, "NABET Accreditation", nabet, chunks=(Chunk.EXTRACTED_PROJECT, Chunk.ACTIVITY)),

    # Block B: Regulatory Position & Legal
    Section("statutory_status", "B", 4, "Brief Description of the Project", statutory_status, chunks=(Chunk.BASIC, Chunk.CAF)),
    Section("undertaking_letterhead", "B", 5, "Undertaking on Letterhead", undertaking_letterhead, chunks=(Chunk.ACTIVITY,)),
    Section("litigation", "B", 6, "Public Complaints and Litigation Status", litigation, chunks=(Chunk.CAF,)),
    Section("earlier_clearances", "B", 22, "Detail of Earlier EC / CTO / Certified Compliance Report", earlier_clearances, chunks=(Chunk.PART_A,)),
    Section("msihc_undertaking", "B", 23, "Notarized Undertaking under MSIHC Rules, 1989", msihc_undertaking, chunks=(Chunk.SAFETY,)),

    # Block C: Project Description, Products & Process
    Section("key_metrics", "C", 7, "Brief Description of the Project (Key Metrics)", key_metrics, chunks=(Chunk.BASIC, Chunk.WATER_BALANCE, Chunk.WASTEWATER, Chunk.AIR_EMISSIONS)),
    Section("land_breakup", "C", 8, "Land Break-up and Area Adequacy", land_breakup, chunks=(Chunk.BASIC,)),
    Section("land_documents", "C", 24, "Land Documents", land_documents, chunks=(Chunk.ACTIVITY,)),
    Section("product_list", "C", 21, "List of Products", product_list, chunks=(Chunk.PRODUCTS,)),
    Section("raw_materials", "C", 16, "Product-wise Raw Materials", raw_materials, chunks=(Chunk.RAW_MATERIALS,)),
    Section("manufacturing_process", "C", 17, "Manufacturing Process and Plant & Machinery", manufacturing_process, chunks=(Chunk.PROCESS, Chunk.ACTIVITY)),

    # Block D: Location, Siting & Setting
    Section("maps", "D", 9, "Location of Project and its Connectivity", maps, chunks=(Chunk.ACTIVITY,)),
    Section("layout_plan", "D", 10, "Layout of the Project Site", layout_plan, chunks=(Chunk.ACTIVITY,)),
    Section("siting_criteria", "D", 11, "Siting Criteria", siting_criteria, chunks=(Chunk.SITING,)),
    Section("sensitivity_screening", "D", 12, "Environmental Sensitivity Screening", sensitivity_screening, chunks=(Chunk.SITING,)),

    # Block E: Resource Demands & Emissions
    Section("water_balance_table", "E", 13, "Water Requirement and Water Balance", water_balance_table, chunks=(Chunk.WATER_BALANCE,)),
    Section("wastewater_generation", "E", 14, "Wastewater Generation", wastewater_generation, chunks=(Chunk.WASTEWATER,)),
    Section("wastewater_treatability", "E", 25, "Wastewater Treatability and Characteristics", wastewater_treatability, chunks=(Chunk.WASTEWATER,)),
    Section("flue_and_process_gas", "E", 15, "Air Act / Flue Gas and Process Gas Emissions", flue_and_process_gas, chunks=(Chunk.AIR_EMISSIONS,)),
    Section("fugitive_ldar", "E", 18, "Action Plan to Control and Monitor Fugitive Emissions", fugitive_ldar, chunks=(Chunk.AIR_EMISSIONS,)),

    # Block F: Waste & Hazard Management
    Section("hazardous_waste", "F", 26, "Hazardous Waste Management Matrix", hazardous_waste, chunks=(Chunk.HAZARDOUS_WASTE,)),
    Section("non_hazardous_waste", "F", 27, "Non-Hazardous Waste Management", non_hazardous_waste, chunks=(Chunk.NON_HAZARDOUS_WASTE,)),
    Section("general_safety", "F", 28, "Safety Measures (General)", general_safety, chunks=(Chunk.SAFETY,)),
    Section("fire_and_peso", "F", 29, "Fire Protection Plan / PESO Compliance", fire_and_peso, chunks=(Chunk.SAFETY,)),
    Section("nearest_fire_station", "F", 30, "Nearest Fire Station", nearest_fire_station, chunks=(Chunk.SAFETY,)),
    Section("hazardous_storage", "F", 31, "Storage Details of Hazardous Chemicals and Safety Measures", hazardous_storage, chunks=(Chunk.STORAGE_PESO,)),

    # Block G: EMP & Closing
    Section("threshold_compliance", "G", 19, "Compliance with EIA Notification 2006 Threshold Conditions", threshold_compliance, chunks=(Chunk.BASIC, Chunk.SITING)),
    Section("emp_cost_table", "G", 20, "Environment Management Plan (Cost Table)", emp_cost_table, chunks=(Chunk.BASIC,)),
    Section("prayer", "G", 35, "Request to the Committee", prayer, chunks=(Chunk.BASIC,)),
    Section("thank_you", "G", 36, "Thank You", thank_you, chunks=(Chunk.BASIC,), structural=True),
)

DECK = DeckSpec(
    name=CHEMICAL_TOR_DECK,
    title="Terms of Reference (Sector 5f)",
    sections=SECTIONS,
    blocks=BLOCKS,
    filename_prefix="Chemical_ToR_Presentation",
)
