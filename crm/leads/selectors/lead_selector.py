# crm/leads/selectors/lead_selector.py
# Lead selectors for data retrieval

from django.db.models import Q
from typing import Optional, List
from crm.leads.models import Lead


def get_lead(lead_id: int, for_update: bool = False) -> Optional[Lead]:
    """Get a single lead by ID."""
    qs = Lead.objects.all()
    if for_update:
        qs = qs.select_for_update()
    
    try:
        return qs.get(id=lead_id)
    except Lead.DoesNotExist:
        return None


def get_lead_for_update(lead_id: int) -> Optional[Lead]:
    """Get a lead locked for update (for conversion)."""
    return get_lead(lead_id, for_update=True)


def list_leads(
    *,
    search: Optional[str] = None,
    status: Optional[str] = None,
    rating: Optional[str] = None,
    source: Optional[str] = None,
    owner_id: Optional[int] = None,
    is_active: bool = True,
    order_by: str = '-created_at'
):
    """List leads with optional filtering."""
    qs = Lead.objects.all()
    
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(company_name__icontains=search) |
            Q(primary_email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    if status:
        qs = qs.filter(status=status)
    
    if rating:
        qs = qs.filter(rating=rating)
    
    if source:
        qs = qs.filter(source=source)
    
    if owner_id:
        qs = qs.filter(owner_id=owner_id)
    
    return qs.order_by(order_by)


def search_leads(query: str, limit: int = 10) -> List[Lead]:
    """Search leads by name, company, email, or phone."""
    return list(
        Lead.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(company_name__icontains=query) |
            Q(primary_email__icontains=query)
        ).order_by('-created_at')[:limit]
    )
