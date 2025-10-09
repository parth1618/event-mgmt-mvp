"""Main API v1 router that includes all endpoint routers."""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    events,
    tickets,
    orders,
    payments,
    categories,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])