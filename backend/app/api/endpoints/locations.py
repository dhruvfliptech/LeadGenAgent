"""
Location endpoints for managing Craigslist locations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, asc, func
from typing import List, Optional, Dict, Any
import json
import os

from app.core.database import get_db
from app.models.locations import Location
from pydantic import BaseModel


class LocationCreate(BaseModel):
    name: str
    code: str
    url: str
    region: Optional[str] = None
    state: Optional[str] = None
    country: str = "US"
    is_active: bool = True


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    state: Optional[str] = None
    is_active: Optional[bool] = None


class LocationResponse(BaseModel):
    id: int
    name: str
    code: str
    url: str
    region: Optional[str]
    state: Optional[str]
    country: str
    is_active: bool
    
    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/", response_model=List[LocationResponse])
async def get_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    region: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of locations with optional filtering."""
    query = select(Location)
    
    # Apply filters
    conditions = []
    if active_only:
        conditions.append(Location.is_active == True)
    if region:
        conditions.append(Location.region == region)
    if country:
        conditions.append(Location.country == country)
    if state:
        conditions.append(Location.state == state)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset(skip).limit(limit).order_by(Location.name)
    
    result = await db.execute(query)
    locations = result.scalars().all()
    
    return locations


@router.get("/tree")
async def get_locations_tree(
    active_only: bool = Query(True),
    region: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Return hierarchical tree: region -> country -> state (optional) -> locations."""
    query = select(Location)

    conditions = []
    if active_only:
        conditions.append(Location.is_active == True)
    if region:
        conditions.append(Location.region == region)
    if country:
        conditions.append(Location.country == country)

    if conditions:
        query = query.where(and_(*conditions))

    query = query.order_by(asc(Location.region), asc(Location.country), asc(Location.state), asc(Location.name))
    result = await db.execute(query)
    rows = result.scalars().all()

    tree: Dict[str, Dict[str, Dict[str, List[Dict[str, Any]]]]] = {}

    for loc in rows:
        reg = loc.region or "Unknown"
        ctry = loc.country or "Unknown"
        st = loc.state or "_"

        tree.setdefault(reg, {})
        tree[reg].setdefault(ctry, {})
        tree[reg][ctry].setdefault(st, [])
        tree[reg][ctry][st].append({
            "id": loc.id,
            "name": loc.name,
            "code": loc.code,
            "url": loc.url,
            "is_active": loc.is_active,
        })

    return tree


@router.get("/us/states")
async def get_us_states(
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Return list of US states with counts of active locations."""
    query = select(Location.state, func.count(Location.id)).where(Location.country == "US")
    if active_only:
        query = query.where(Location.is_active == True)
    query = query.group_by(Location.state).order_by(asc(Location.state))
    result = await db.execute(query)
    rows = result.all()
    # Filter out null states
    return [{"state": s, "count": c} for (s, c) in rows if s]


@router.get("/by_state")
async def get_locations_by_state(
    state: str = Query(...),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Return locations for a given US state."""
    query = select(Location).where(Location.country == "US", Location.state == state)
    if active_only:
        query = query.where(Location.is_active == True)
    query = query.order_by(asc(Location.name))
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "code": loc.code,
            "url": loc.url,
            "state": loc.state,
            "country": loc.country,
            "is_active": loc.is_active,
        }
        for loc in rows
    ]


# --------------- Hierarchy (preloaded JSON or DB fallback) ---------------

HIERARCHY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'data',
    'locations_full.json'
)


def _load_hierarchy_from_file() -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(HIERARCHY_FILE):
            with open(HIERARCHY_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'nodes' in data:
                    return data
    except Exception:
        pass
    return None


def _build_nodes_from_db(rows: List[Location]) -> Dict[str, Any]:
    us_states: Dict[str, List[Dict[str, Any]]] = {}
    world_regions: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for loc in rows:
        if (loc.country or '').upper() == 'US' and loc.state:
            us_states.setdefault(loc.state, []).append({
                'type': 'city', 'label': loc.name, 'id': loc.id, 'code': loc.code, 'url': loc.url,
                'state': loc.state, 'country': loc.country, 'region': loc.region or 'US'
            })
        else:
            region = loc.region or 'World'
            country = loc.country or 'Unknown'
            world_regions.setdefault(region, {}).setdefault(country, []).append({
                'type': 'city', 'label': loc.name, 'id': loc.id, 'code': loc.code, 'url': loc.url,
                'state': loc.state, 'country': loc.country, 'region': loc.region or 'World'
            })

    us_nodes = [{'type': 'state', 'label': st, 'children': sorted(cities, key=lambda c: c['label'])}
                for st, cities in sorted(us_states.items())]
    world_nodes = []
    for region, countries in sorted(world_regions.items()):
        country_nodes = []
        for country, cities in sorted(countries.items()):
            country_nodes.append({'type': 'country', 'label': country, 'children': sorted(cities, key=lambda c: c['label'])})
        world_nodes.append({'type': 'region', 'label': region, 'children': country_nodes})

    return {
        'nodes': [
            {'type': 'group', 'label': 'U.S. Locations', 'children': us_nodes},
            {'type': 'group', 'label': 'World Locations', 'children': world_nodes},
        ]
    }


@router.get("/hierarchy")
async def get_locations_hierarchy(
    db: AsyncSession = Depends(get_db),
    refresh: bool = Query(False)
):
    """Return preloaded full hierarchy or build from DB as fallback."""
    if not refresh:
        file_data = _load_hierarchy_from_file()
        if file_data:
            return file_data

    result = await db.execute(select(Location).order_by(asc(Location.country), asc(Location.state), asc(Location.name)))
    rows = result.scalars().all()
    return _build_nodes_from_db(rows)


def _iter_city_nodes(nodes: List[Dict[str, Any]]):
    for n in nodes:
        if n.get('type') == 'city':
            yield n
        for child in n.get('children') or []:
            yield from _iter_city_nodes(child if isinstance(child, list) else [child])


@router.post("/import_full")
async def import_full_hierarchy(
    payload: Dict[str, Any] = Body(...),
    seed: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Save hierarchy JSON and optionally seed DB with city nodes."""
    if not isinstance(payload, dict) or 'nodes' not in payload:
        raise HTTPException(status_code=400, detail="Payload must contain 'nodes'")

    os.makedirs(os.path.dirname(HIERARCHY_FILE), exist_ok=True)
    with open(HIERARCHY_FILE, 'w') as f:
        json.dump(payload, f)

    created = 0
    if seed:
        existing = await db.execute(select(Location.code))
        existing_codes = {row[0] for row in existing.all()}
        to_add: List[Location] = []
        for city in _iter_city_nodes(payload['nodes']):
            code = city.get('code')
            name = city.get('label') or city.get('name')
            url = city.get('url')
            if not code or not url or not name:
                continue
            if code in existing_codes:
                continue
            to_add.append(Location(
                name=name,
                code=code,
                url=url,
                state=city.get('state'),
                country=city.get('country') or 'US',
                region=city.get('region'),
                is_active=True,
            ))
            existing_codes.add(code)
        if to_add:
            db.add_all(to_add)
            await db.commit()
            created = len(to_add)

    return {"saved": True, "seeded": seed, "locations_created": created}


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(location_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific location by ID."""
    query = select(Location).where(Location.id == location_id)
    result = await db.execute(query)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return location


@router.post("/", response_model=LocationResponse)
async def create_location(location_data: LocationCreate, db: AsyncSession = Depends(get_db)):
    """Create a new location."""
    # Check if code already exists
    query = select(Location).where(Location.code == location_data.code)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Location code already exists")
    
    location = Location(**location_data.model_dump())
    db.add(location)
    await db.commit()
    await db.refresh(location)
    
    return location


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    location_data: LocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing location."""
    query = select(Location).where(Location.id == location_id)
    result = await db.execute(query)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Update fields
    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)
    
    await db.commit()
    await db.refresh(location)
    
    return location


@router.delete("/{location_id}")
async def delete_location(location_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a location (soft delete by setting is_active to False)."""
    query = select(Location).where(Location.id == location_id)
    result = await db.execute(query)
    location = result.scalar_one_or_none()
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    location.is_active = False
    await db.commit()
    
    return {"message": "Location deactivated successfully"}