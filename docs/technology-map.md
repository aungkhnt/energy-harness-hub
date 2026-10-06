# Technology map

The catalog now contains 26 entries. These are not all equivalent kinds of objects:
some describe resources, some fueled plants, and some reusable conversion devices.
The `energy_role` field makes this distinction explicit. A particular plant combines
a resource, one or more converters, auxiliary systems, and an electrical endpoint.

## Families beyond the original six

| Group | Added entries | Main questions to model later |
|---|---|---|
| Water | Hydropower; river/ocean current power | Head or velocity, flow availability, hydraulic losses, site constraints |
| Earth heat | Geothermal | Temperature, flow, reservoir behavior, drilling, pumping and heat rejection |
| Marine | Tidal; wave; ocean thermal; salinity gradient | Local resource, conversion performance, survivability, pumping/membranes, maintenance |
| Combustion | Natural gas; coal; liquid fuel | Fuel energy, conversion cycle, fuel supply, emissions, cooling and dispatch |
| Bioenergy and waste | Biomass/biogas; waste-to-energy | Feedstock composition, preprocessing, supply radius, residue treatment |
| Electrochemical | Fuel cells | Fuel provenance, stack efficiency/degradation, auxiliary demand |
| Heat recovery | Waste-heat electricity | Source temperature and duration, cold sink, parasitic power, host-system effects |
| Nuclear decay | Radioisotope power | Decay heat, conversion efficiency, mass and mission lifetime |
| Direct conversion | Thermoelectric; thermionic; thermoradiative | Hot/cold conditions, device properties, current-voltage behavior |
| Small-scale harvesting | Mechanical; RF | Available excitation or radiation, conversion and conditioning losses |

The original TPV, solar PV, solar thermal, wind, fission, and fusion entries remain.
Family-level references are in [the evidence manifest](../evidence/references.md).
Specialist entries lacking a specific reference are marked in the machine-readable
catalog. No deployment maturity or profitability is inferred from their inclusion.

## Things that are not additional primary energy sources

- Batteries, pumped storage, compressed/liquid air, flywheels, thermal storage,
  gravity storage, and manufactured hydrogen or synthetic fuels return previously
  supplied energy, with conversion losses. Their upstream inputs must be included.
- Fuel cells convert a supplied fuel. Hydrogen origin and production costs must be
  stated before describing a hydrogen system's overall efficiency or economics.
- Rankine, Brayton, organic Rankine, Stirling, and related cycles are conversion
  approaches reusable across different sources, not independent energy resources.
- Combined heat and power is a multi-output system pattern. Hybrid plants combine
  families. Space-based solar adds collection, transmission, and reception stages.

An archetype is a discovery label, not a promise of implemented behavior. For example,
the hydropower reference supports a prescribed head/flow operating point; it does
not simulate reservoir scheduling merely because the catalog lists reservoirs.

## Immediate implementation sequence

Completed in this pass: expanded taxonomy, shared run/result interface, TPV reference
calculation, a second model (hydropower), illustrative economics, reports, and tests.

Current priority (2026-09-18): the [engine backbone](backbone.md), network/equation
interfaces, and study infrastructure. Device calibration and coupled heat balance
are deferred to a later batch. Hydropower was
selected as the second reference because its closed-form equation offers a clear
check of shared electrical accounting without another large solver dependency.

Supply-chain analysis needs quantities, specifications, locations, dated prices,
and evidence about availability. Capital line items are the first input structure,
not an implemented supply-chain forecast.
