"""Deterministic synthetic records replacing the unavailable warehouse for local demos."""
from collections import Counter
from datetime import date

PROGRAMS = [
    dict(name='Aurora EV', code='AU-01', gi='DEMO-001', effective='DEMO-EP-01'),
    dict(name='Orion Hybrid', code='OR-02', gi='DEMO-002', effective='DEMO-EP-02'),
]
PMTS = ['100', '200', '300', '400', '500', '600']
COMMODITIES = {'CPSC-001': 'Body', 'CPSC-002': 'Chassis', 'CPSC-003': 'Electrical'}
TEAMS = ['Structures', 'Dynamics', 'Electronics']
SNAPSHOTS = ['2026-07-01', '2026-08-01', '2026-09-01']
MILESTONES = {'concept': '2026-01-15', 'prototype': '2026-04-15', 'validation': '2026-07-15', 'launch': '2026-11-15'}
STATES = ['Meet', 'Unassessed', 'Does Not Meet', 'Approved Deviation', 'Cannot Assess', 'Not Applicable']

# Source-grain records: program × team × commodity × PMT × snapshot × assessment.
ASSESSMENTS = []
for pi, program in enumerate(PROGRAMS):
    for si, snapshot in enumerate(SNAPSHOTS):
        for ti, team in enumerate(TEAMS):
            for ci, cpsc in enumerate(COMMODITIES):
                for mi, pmt in enumerate(PMTS):
                    for n in range(20):
                        score = (n + ci + mi + ti + pi) % 20
                        state = ('Meet' if score < 10 + si else
                                 'Unassessed' if score < 15 else
                                 'Does Not Meet' if score < 17 else STATES[score - 14])
                        ASSESSMENTS.append(dict(
                            gi_code=program['gi'], program_name=program['name'],
                            snapshot_date=snapshot, dvp_team=team, cpsc=cpsc, pmt_code=pmt,
                            assessment_id=f'DEMO-{pi+1}-{ti+1}-{ci+1}-{mi+1}-{n+1:02}',
                            conf_state=state, with_evidence=score < 12 + si,
                            classification=['applicable', 'carryover', 'not_applicable', 'unclassified'][score % 4],
                        ))

COSTS = [dict(program=p['name'], effectivein=p['effective'], pmt=pmt, cpsc=cpsc,
              cpsc_name=name, partnumber=f'DEMO-PART-{pi+1}{ci+1}{mi+1}',
              actual_tooling_cost=10000 + 1500*pi + 700*ci + 300*mi,
              target_tooling_cost=12000 + 500*ci,
              actual_piece_cost=100 + 15*pi + 10*ci + 5*mi,
              target_piece_cost=125 + 8*ci, currency='USD', source_reference='Synthetic fixture')
         for pi,p in enumerate(PROGRAMS) for ci,(cpsc,name) in enumerate(COMMODITIES.items())
         for mi,pmt in enumerate(PMTS)]


def selected_program(q):
    for p in PROGRAMS:
        if any(q.get(k) == p[v] for k,v in [('gi_code','gi'),('gi_id','gi'),('program_names','name'),('program_name','name'),('program_codes','code'),('effectivein','effective')]):
            return p
    return PROGRAMS[0]


def records(q):
    p = selected_program(q)
    snapshot = q.get('snapshot_date') or SNAPSHOTS[-1]
    if snapshot == 'null': snapshot = SNAPSHOTS[-1]
    filters = dict(gi_code=p['gi'], snapshot_date=snapshot, cpsc=q.get('cpsc'),
                   pmt_code=q.get('pmt_code') or q.get('pmt'), dvp_team=q.get('dvp_team'))
    return [r for r in ASSESSMENTS if all(not v or v == 'null' or r[k] == v for k,v in filters.items())]


def conf(rows):
    counts = Counter(r['conf_state'] for r in rows)
    return {s: counts[s] for s in STATES}


def metrics(rows):
    c = conf(rows)
    return dict(meet=c['Meet'], unassessed=c['Unassessed'], does_not_meet=c['Does Not Meet'],
                approved_deviation=c['Approved Deviation'], cannot_assess=c['Cannot Assess'],
                not_applicable=c['Not Applicable'], co=c['Cannot Assess']+c['Not Applicable'],
                carryover=c['Cannot Assess']+c['Not Applicable'], total_assessments=len(rows))


def cost_data(q, kind):
    p = selected_program(q)
    data = [dict(r, gap=r[f'actual_{kind}_cost']-r[f'target_{kind}_cost']) for r in COSTS
            if r['program'] == p['name'] and (not q.get('cpsc') or r['cpsc'] == q['cpsc'])
            and (not q.get('pmt_code') or r['pmt'] == q['pmt_code'])]
    return dict(effectivein=p['effective'], cpsc=q.get('cpsc'), pmt_code=q.get('pmt_code'),
                cost_type=kind, data=data, total_records=len(data),
                total_cost=sum(r[f'actual_{kind}_cost'] for r in data))


def response(path, q):
    p = selected_program(q)
    query = (q.get('query') or q.get('q') or '').lower()
    search = lambda values: [v for v in values if query in v.lower()]
    rows = records(q)
    if path == '/search/model-years': return search(['2026', '2027'])
    if path == '/search/program-names': return search([x['name'] for x in PROGRAMS])
    if path == '/search/program-codes': return search([p['code']] if q.get('program_name') else [x['code'] for x in PROGRAMS])
    if path == '/vehicle-line/':
        if q.get('program_codes') not in [x['code'] for x in PROGRAMS]: raise ValueError('Unknown demo program code')
        if q.get('model_year') not in ['2026','2027']: raise ValueError('Unknown demo model year')
        return dict(gi_code=p['gi'], program_code=p['name'], vehicle_line=p['name'],
                    affected_plant='Demo Plant', plant_code='DP', wers_plant='DP', model_year=q['model_year'],
                    milestones={key: value + 'T12:00:00' for key, value in MILESTONES.items()}, summary=f"Project Description: {p['name']} (Demo Plant) | ptvl: Demo Platform | Effective Point: {p['effective']}")
    if path.endswith('/snapshots'): return dict(gi_code=p['gi'], snapshots=SNAPSHOTS)
    if path == '/pmt/list': return dict(pmt_codes=PMTS, mapping={}, count=len(PMTS))
    if 'cpsc' in path and path.endswith(('/list','/cpsc-list','/autocomplete')):
        return dict(gi_code=p['gi'], cpsc_codes=search(COMMODITIES), count=len(search(COMMODITIES)))
    if 'dvp-teams/autocomplete' in path: return dict(dvp_teams=search(TEAMS))
    if path.endswith('/by-dvp-team/row'): return dict(result=rows[0] if rows else None)
    if path.endswith('/metrics/dvp-team-list'):
        return dict(dvp_teams_metrics=[dict(dvp_team=t,conf_state_summary=conf([r for r in rows if r['dvp_team']==t])) for t in TEAMS])
    if '/metrics/conf-state' in path: return dict(conf_state_summary=conf(rows))
    if path.endswith('/cpsc-conf-state-breakdown'):
        return dict(cpsc_metrics={c:dict(name=c,conf_state_breakdown=conf([r for r in rows if r['cpsc']==c])) for c in COMMODITIES})
    if path.endswith('/dvp-classification'):
        classified = sum(r['classification'] != 'unclassified' for r in rows)
        return dict(program=p['name'],total=len(rows),classified=classified,not_classified=len(rows)-classified,percentage=100*classified/len(rows) if rows else 0)
    if path.endswith(('/cae-graph','/cae-total-assessments','/dr-evidences-by-assessment')):
        data = [dict(program=p['name'],cpsc=c,cpsc_code=c,assessment_id='Demo Assessment',total_unique_dvp_teams=3,
                     **metrics([r for r in rows if r['cpsc']==c])) for c in COMMODITIES if any(r['cpsc']==c for r in rows)]
        return dict(data=data)
    if path.endswith('/design-rule-classification'):
        return dict(data=[dict(Counter(r['classification'] for r in rows))])
    if path.endswith('/hir-completion'):
        data=[]
        for c in COMMODITIES:
            group=[r for r in rows if r['cpsc']==c]
            if not group: continue
            evidence=sum(r['with_evidence'] for r in group)
            data.append(dict(program_name=p['name'],gi_code=p['gi'],cpsc=c,pmt_code=q.get('pmt_code'),
                             milestone_date=q.get('milestone_date'),dvp_team=q.get('dvp_team'),with_evidence=evidence,
                             without_evidence=len(group)-evidence,total_items=len(group),completion_percentage=100*evidence/len(group)))
        return dict(gi_code=p['gi'],data=data,total_records=len(data))
    if path.startswith('/api/v1/milestone-readiness/'):
        milestone=q.get('milestone','validation')
        percentage=round(100*sum(r['conf_state']=='Meet' for r in rows)/len(rows)) if rows else 0
        return dict(program=p['name'],milestone=milestone,milestone_date=MILESTONES.get(milestone),
                    metrics=[dict(source=s,target=90,actual=percentage,percentage=percentage,status='green' if percentage>=90 else 'yellow' if percentage>=60 else 'red') for s in ['CAE','DVP','HIR','Design Rules','DPA5','Costs']])
    if path == '/dpa5/summary':
        c=conf(rows); total=len(rows)
        summary=dict(compliant=c['Meet'],not_compliant=c['Does Not Meet'],not_assessable=total-c['Meet']-c['Does Not Meet'],total=total)
        glidepath=[]
        for i,(name,day) in enumerate(MILESTONES.items()):
            compliant=int(total*(.3+.15*i)); non=int(total*(.35-.08*i))
            glidepath.append(dict(milestone_name=name,milestone_date=day,compliant=compliant,not_compliant=non,
                                 not_assessable=total-compliant-non,assessment_goal_curve=50+15*i,compliance_goal_curve=40+15*i,compliance_prediction=45+15*i))
        return dict(gi_code=p['gi'],summary=summary,glidepath=glidepath)
    if path.startswith('/api/v1/dvp-glidepath/'):
        if path.endswith('/pmts'): return PMTS
        if path.endswith('/milestones'): return list(MILESTONES.values())
        if path.endswith('/data'):
            data=[]
            for i,(name,day) in enumerate(MILESTONES.items()):
                if q.get('milestone') and q['milestone'] not in [name,day]: continue
                total=len(rows); meet=int(total*(.4+.15*i)); non=int(total*(.25-.05*i))
                data.append(dict(gi_code=p['gi'],pmt_code=q.get('pmt') or 'All',model_year='2026',milestone=name,
                                 scheduled_finished=day,actual_finished=day,metrics=dict(meet=meet,does_not_meet=non,unassessed=total-meet-non,total=total)))
            return dict(data=data)
    if path.startswith('/cost/'):
        data=cost_data(q,'piece')['data']
        commodities=[dict(cpsc=c,name=n) for c,n in COMMODITIES.items()]
        if path.endswith('/pmt/list'): return dict(pmt_codes=PMTS,count=len(PMTS))
        if path.endswith('/dropdowns'): return dict(effectivein=p['effective'],partnumbers=[r['partnumber'] for r in data],commodities=commodities,vehicle_lines=[p['name']])
        if path.endswith('/partnumber/list'): return dict(part_numbers=search([r['partnumber'] for r in data]),count=len(data))
        if path.endswith('/commodity/list'): return dict(commodities=commodities,count=len(commodities))
        if path.endswith('/vehicleline/list'): return dict(vehicle_lines=[p['name']],count=1)
        if path.endswith('/metrics/tooling'): return cost_data(q,'tooling')
        if path.endswith('/metrics/piece'): return cost_data(q,'piece')
        if path.endswith('/metrics/combined'):
            tooling=cost_data(q,'tooling'); piece=cost_data(q,'piece')
            return dict(tooling_cost=tooling,piece_cost=piece,summary=dict(total_tooling_cost=tooling['total_cost'],
                total_piece_cost=piece['total_cost'],grand_total_cost=tooling['total_cost']+piece['total_cost'],
                total_tooling_records=tooling['total_records'],total_piece_records=piece['total_records']))
    raise KeyError(f'No mock endpoint for {path}')
