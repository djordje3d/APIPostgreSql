from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app import schemas
from app.services.dashboard_analytics import (
    compute_spot_ticket_counts,
    compute_total_outstanding,
    count_unpaid_and_partial,
    sum_payments_in_range,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/analytics",
    response_model=schemas.DashboardAnalyticsResponse,
    summary="Dashboard analytics (status + revenue)",
    description=(
        "Returns spot/ticket counts and revenue/outstanding in one response. "
        "Pass today, month_from, month_to as calendar dates (YYYY-MM-DD) "
        "matching the dashboard client (typically local date strings)."
    ),
)
def dashboard_analytics(
    db: Session = Depends(get_db),
    garage_id: int | None = Query(default=None),
    today: date = Query(
        ...,
        description=("Calendar date for 'today' revenue (inclusive, UTC day bounds)."),
    ),
    month_from: date = Query(
        ...,
        description="First day of month (inclusive).",
    ),
    month_to: date = Query(
        ...,
        description="Last day of month (inclusive).",
    ),
):
    free, occupied, inactive, open_t = compute_spot_ticket_counts(db, garage_id)
    today_rev = sum_payments_in_range(db, garage_id, today, today)
    month_rev = sum_payments_in_range(db, garage_id, month_from, month_to)
    unpaid_partial = count_unpaid_and_partial(db, garage_id)
    outstanding = compute_total_outstanding(db, garage_id)

    return schemas.DashboardAnalyticsResponse(
        free_spots=free,
        occupied_spots=occupied,
        inactive_spots=inactive,
        open_tickets=open_t,
        today_revenue=today_rev,
        month_revenue=month_rev,
        unpaid_partially_paid_count=unpaid_partial,
        total_outstanding=outstanding,
    )
