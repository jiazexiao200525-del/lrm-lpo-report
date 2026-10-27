"""Read existing summaries and check local report structure; does not parse DFT logs."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from decimal import Decimal
import json
import math

web = Path(__file__).resolve().parent
project = web.parent
def read(rel):
    return json.loads((project / rel).read_text(encoding='utf-8-sig'))

class AuditHTML(HTMLParser):
    void = set('area base br col embed hr img input link meta param source track wbr'.split())
    def __init__(self):
        super().__init__()
        self.stack, self.ids, self.refs, self.errors = [], [], [], []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d:
            self.ids.append(d['id'])
        for key in ('href', 'src', 'data-src'):
            if d.get(key):
                self.refs.append(d[key])
        if tag not in self.void:
            self.stack.append(tag)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void:
            self.handle_endtag(tag)
    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            self.errors.append('Unexpected close: ' + tag)
        else:
            self.stack.pop()

p = AuditHTML()
p.feed((web / 'index.html').read_text(encoding='utf-8'))
assert not p.errors and not p.stack, (p.errors, p.stack)
assert len(p.ids) == len(set(p.ids)), 'Duplicate IDs'
for ref in p.refs:
    u = urlsplit(ref)
    if u.scheme or u.netloc:
        continue
    target = (web / unquote(u.path)).resolve() if u.path else web / 'index.html'
    assert target.exists(), str(target)
    if u.fragment and target.name == 'index.html':
        assert u.fragment in p.ids, u.fragment

b = read('pdos_combined_d8f1704e_20261023/binding_energy_summary_20261026.json')
c = read('charge_difference_d8f1704e_20261023/charge_analysis.json')
d = read('pdos_combined_d8f1704e_20261023/processed/pdos_near_fermi_summary.json')
m = read('mulliken_reanalysis_d8f1704e_20261027/mulliken_reanalysis_summary.json')
energies = [Decimal(v) for v in b['total_energies_eV'].values()]
ebind = energies[0] - energies[1] - energies[2]
assert abs(ebind - Decimal(b['binding_energy_eV_per_simulation_cell'])) < Decimal('1e-9')
assert math.isclose(c['LRM_halfspace_delta_e'] + c['LPO_halfspace_delta_e'], c['net_electrons'], abs_tol=1e-12)
for phase, t in m['phase_transfer'].items():
    rows = [x for x in m['element_summary'] if x['phase'] == phase]
    assert math.isclose(sum(x['delta_electrons_sum_e'] for x in rows), t['delta_electrons_sum_e'], abs_tol=1e-10)
    assert sum(x['n'] for x in rows) == (97 if phase == 'LRM' else 95)
a, bare = d['cases'][:2]
result = {
    'date': '2026-10-27',
    'scope': 'Existing structured summaries and HTML; no new DFT calculation or structural acceptance',
    'html': {'balanced_tags': True, 'unique_ids': len(p.ids), 'local_references_checked': len(p.refs), 'missing_targets': []},
    'binding_eV_cell': str(ebind),
    'interface_count_from_existing_structure_audit': 1,
    'area_A2': c['interface_area_A2'],
    'frozen_separation_work_J_m2': -float(ebind) / c['interface_area_A2'] * 16.02176634,
    'O_p_at_EF_percent': a['O-p_D_EF_cell'] / a['D_EF_TDOS_states_per_eV_cell'] * 100,
    'LRM_phase_at_EF_percent': d['interface_phase']['LRM']['D_EF_cell'] / a['D_EF_TDOS_states_per_eV_cell'] * 100,
    'Mn_d_EF_decrease_percent': (1 - a['Mn-d_D_EF_cell'] / bare['Mn-d_D_EF_cell']) * 100,
    'LRM_phase_EF_decrease_percent': (1 - d['interface_phase']['LRM']['D_EF_cell'] / bare['D_EF_TDOS_states_per_eV_cell']) * 100,
    'Mn_d_minus0p5_to0_change_states': a['Mn-d_integral_minus0p5_to0'] - bare['Mn-d_integral_minus0p5_to0'],
    'LRM_phase_minus0p5_to0_change_states': d['interface_phase']['LRM']['integral_minus0p5_to0'] - bare['integral_TDOS_minus0p5_to0_states'],
    'mulliken_element_sums_verified': True,
    'mulliken_population_residual_e': sum(x['delta_electrons_sum_e'] for x in m['phase_transfer'].values()),
    'density_integral_residual_e': c['net_electrons'],
    'LPO_halfspace_sensitivity_range_e': [min(x['LPO_delta_e'] for x in c['split_sensitivity']), max(x['LPO_delta_e'] for x in c['split_sensitivity'])]
}
(web / 'audit_checks_20261027.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
