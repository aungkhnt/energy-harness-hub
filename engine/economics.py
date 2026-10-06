"""Transparent constant-output lifecycle case; no live prices or supply database."""
from .validation import exact_fields, metric
from .physics import positive, integer


def assess(net_power_w, case):
    exact_fields(case, ['currency', 'price_year', 'region', 'assumption_status',
                        'lifetime_years', 'real_discount_rate', 'operating_hours_per_year',
                        'capital_items', 'annual_opex', 'decommissioning_cost'])
    for key in ('currency', 'region'):
        if not isinstance(case[key], str) or not case[key].strip():
            raise ValueError(f'{key} must be a nonempty string')
    if len(case['currency']) != 3 or not case['currency'].isalpha() or not case['currency'].isupper():
        raise ValueError('currency must be a three-letter uppercase code')
    if case['assumption_status'] != 'illustrative_not_market_data':
        raise ValueError('This economic implementation only supports explicitly illustrative cases')
    integer('price_year',case['price_year'],1900,2200)
    years = integer('lifetime_years',case['lifetime_years'],1,100)
    rate = positive('real_discount_rate',case['real_discount_rate'],allow_zero=True)
    if rate > 1:
        raise ValueError('real_discount_rate must be <= 1')
    hours = positive('operating_hours_per_year',case['operating_hours_per_year'])
    if hours > 8760:
        raise ValueError('operating_hours_per_year must be <= 8760 for this 365-day model')
    positive('net_power_w for LCOE',net_power_w)
    for key in ('annual_opex','decommissioning_cost'):
        positive(key,case[key],allow_zero=True)
    if not isinstance(case['capital_items'],list) or not case['capital_items']:
        raise ValueError('capital_items must be a nonempty list')
    totals = []
    names = set()
    for item in case['capital_items']:
        exact_fields(item,['name','quantity','quantity_unit','unit_cost'])
        if any(not isinstance(item[k],str) or not item[k].strip() for k in ('name','quantity_unit')):
            raise ValueError('Capital item names and quantity units must be nonempty strings')
        if item['name'] in names:
            raise ValueError('Duplicate capital item name')
        names.add(item['name'])
        quantity = positive('quantity',item['quantity'])
        price = positive('unit_cost',item['unit_cost'],allow_zero=True)
        totals.append({**item,'total_cost':quantity*price})
    capex = sum(item['total_cost'] for item in totals)
    annual_kwh = net_power_w/1000*hours
    discount_sum = sum((1+rate)**(-year) for year in range(1,years+1))
    costs = capex + case['annual_opex']*discount_sum + case['decommissioning_cost']/(1+rate)**years
    energy = annual_kwh*discount_sum
    return {
        'status':'illustrative_not_market_data', 'basis':case,
        'capital_breakdown':totals,
        'metrics': {
            'initial_capital_cost':metric(capex,case['currency'],'listed capital items only'),
            'annual_delivered_energy':metric(annual_kwh,'kWh/year','constant modeled net power times assumed operating hours'),
            'discounted_lifecycle_cost':metric(costs,case['currency'],'listed costs; initial capital at year zero; other costs at year end'),
            'lcoe':metric(costs/energy,case['currency']+'/kWh','discounted listed costs / discounted net delivered electricity')},
        'warnings':[
            'Illustrative user-entered prices; no market-price or supply-chain evidence.',
            'Constant net output during assumed operating hours; availability is not predicted.',
            'Constant real costs; no escalation, degradation, financing schedule, taxes, subsidies, or replacement schedule.',
            'Omitted costs are not proven zero. Include fuel and heat-source costs in annual_opex when relevant.',
            'Not suitable for a cross-technology ranking without matching scope and completeness.'
        ]}
