from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from vambora.adapters.inbound.http.dependencies import Container, container
from vambora.adapters.inbound.http.schemas.alert import AlertRuleDTO, CreateAlertRuleRequest
from vambora.domain.alerts import AlertError

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/rules", response_model=AlertRuleDTO, status_code=201)
async def create_rule(
    body: CreateAlertRuleRequest,
    c: Container = Depends(container),
) -> AlertRuleDTO:
    try:
        rule = await c.register_alert_rule(
            device_id=body.device_id,
            line_short_name=body.line_short_name,
            stop_id=body.stop_id,
            threshold_minutes=body.threshold_minutes,
        )
    except AlertError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AlertRuleDTO.from_domain(rule)


@router.get("/rules", response_model=list[AlertRuleDTO])
async def list_rules(
    device_id: str = Query(..., min_length=1),
    c: Container = Depends(container),
) -> list[AlertRuleDTO]:
    rules = await c.list_alert_rules(device_id)
    return [AlertRuleDTO.from_domain(r) for r in rules]


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(
    rule_id: str,
    c: Container = Depends(container),
) -> Response:
    deleted = await c.delete_alert_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="rule not found")
    return Response(status_code=204)
