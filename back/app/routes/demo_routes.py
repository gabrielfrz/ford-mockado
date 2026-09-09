from io import BytesIO
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from app.services.demo_service import response, records, cost_data

router = APIRouter()

@router.get('/export/{report}')
def export(report: str, request: Request):
    if report not in ['dvp-team-assessment','hir','design-rule','costs','dpa5','cae-status']:
        raise HTTPException(404, 'Unknown demo export')
    q = dict(request.query_params)
    data = cost_data(q, 'tooling' if q.get('cost_type') == 'tooling' else 'piece')['data'] if report == 'costs' else records(q)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Synthetic demo data'
    if data:
        fields = list(data[0])
        sheet.append(fields)
        for row in data: sheet.append([row.get(field) for field in fields])
        sheet.freeze_panes = 'A2'
        sheet.auto_filter.ref = sheet.dimensions
    info = workbook.create_sheet('About')
    info.append(['DEMO — All records are synthetic.'])
    info.append(['Report', report])
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return StreamingResponse(stream, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                             headers={'Content-Disposition': f'attachment; filename="demo-{report}.xlsx"'})

@router.get('/{path:path}')
def mock_endpoint(path: str, request: Request):
    try:
        return response('/' + path, dict(request.query_params))
    except KeyError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
