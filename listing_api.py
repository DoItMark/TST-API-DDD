"""
Item Management API - Domain-Driven Design Implementation
Based on Listing Aggregate Root from ItemManagement_ClassDiagram
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime


# Enums
class ItemState(str, Enum):
    ACTIVE = "Active"
    SOLD = "Sold"
    DELISTED = "Delisted"


class ReasonType(str, Enum):
    OUT_OF_STOCK = "OutOfStock"
    POLICY_VIOLATION = "PolicyViolation"
    SELLER_REQUEST = "SellerRequest"
    QUALITY_ISSUE = "QualityIssue"


# Value Objects
class Money(BaseModel):
    amount: Decimal = Field(..., description="Price amount")
    currency: str = Field(default="USD", description="Currency code")

    class Config:
        frozen = True


class Condition(BaseModel):
    score: int = Field(..., ge=1, le=10, description="Condition score (1-10)")
    detailed_description: str = Field(..., description="Detailed condition description")
    known_defects: List[str] = Field(default_factory=list, description="List of known defects")

    class Config:
        frozen = True


class DelistReason(BaseModel):
    reason_type: ReasonType = Field(..., description="Type of delist reason")
    detail: str = Field(..., description="Detailed explanation")

    class Config:
        frozen = True


class Filter(BaseModel):
    name: str = Field(..., description="Filter name")
    value: str = Field(..., description="Filter value")

    class Config:
        frozen = True


# Entities
class Attribute(BaseModel):
    attribute_id: UUID = Field(default_factory=uuid4, description="Unique attribute ID")
    name: str = Field(..., description="Attribute name")
    value: str = Field(..., description="Attribute value")

    def update_value(self, new_value: str) -> None:
        """Update the attribute value"""
        self.value = new_value


# Domain Events
class ListingIndexedEvent(BaseModel):
    listing_id: UUID = Field(..., description="Listing ID")
    relevance_score: float = Field(..., description="Search relevance score")
    item_state: ItemState = Field(..., description="Current item state")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Read Model
class SearchIndexModel(BaseModel):
    index_id: UUID = Field(..., description="Index ID (same as ListingId)")
    searchable_text: str = Field(..., description="Concatenated searchable content")
    relevance_score: float = Field(..., description="Search relevance score")
    search_filters: List[Filter] = Field(default_factory=list, description="Applied filters")

    def update_from_listing(self, listing: 'Listing') -> None:
        """Update search index from listing data"""
        self.searchable_text = f"{listing.title} {' '.join([attr.name + ' ' + attr.value for attr in listing.attributes])}"
        self.relevance_score = self._calculate_relevance(listing)

    def _calculate_relevance(self, listing: 'Listing') -> float:
        """Calculate relevance score based on listing properties"""
        score = 1.0
        if listing.item_state == ItemState.ACTIVE:
            score += 0.5
        if listing.attributes:
            score += len(listing.attributes) * 0.1
        return min(score, 10.0)


# Aggregate Root
class Listing(BaseModel):
    listing_id: UUID = Field(default_factory=uuid4, description="Unique listing ID")
    seller_id: UUID = Field(..., description="Seller's unique ID")
    title: str = Field(..., min_length=1, max_length=200, description="Listing title")
    item_state: ItemState = Field(default=ItemState.ACTIVE, description="Current state of the item")
    price: Money = Field(..., description="Item price")
    condition: Condition = Field(..., description="Item condition details")
    attributes: List[Attribute] = Field(default_factory=list, description="Custom attributes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def activate_listing(self) -> None:
        """Activate the listing"""
        if self.item_state == ItemState.SOLD:
            raise ValueError("Cannot activate a sold listing")
        self.item_state = ItemState.ACTIVE
        self.updated_at = datetime.utcnow()

    def delist_listing(self, reason: DelistReason) -> None:
        """Delist the listing with a reason"""
        if self.item_state == ItemState.DELISTED:
            raise ValueError("Listing is already delisted")
        self.item_state = ItemState.DELISTED
        self.updated_at = datetime.utcnow()
        # In a real implementation, store the reason in event log

    def update_price(self, new_price: Money) -> None:
        """Update the listing price"""
        if self.item_state == ItemState.SOLD:
            raise ValueError("Cannot update price of a sold listing")
        self.price = new_price
        self.updated_at = datetime.utcnow()

    def publish_listing_indexed_event(self) -> ListingIndexedEvent:
        """Publish a listing indexed event"""
        return ListingIndexedEvent(
            listing_id=self.listing_id,
            relevance_score=self._calculate_relevance_score(),
            item_state=self.item_state
        )

    def _calculate_relevance_score(self) -> float:
        """Calculate relevance score for search indexing"""
        score = 1.0
        if self.item_state == ItemState.ACTIVE:
            score += 2.0
        if self.condition.score >= 8:
            score += 1.0
        if self.attributes:
            score += len(self.attributes) * 0.2
        return min(score, 10.0)


# Request/Response Models
class CreateListingRequest(BaseModel):
    seller_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    price: Money
    condition: Condition
    attributes: Optional[List[Attribute]] = []


class UpdatePriceRequest(BaseModel):
    new_price: Money


class DelistRequest(BaseModel):
    reason: DelistReason


class ListingResponse(BaseModel):
    listing_id: UUID
    seller_id: UUID
    title: str
    item_state: ItemState
    price: Money
    condition: Condition
    attributes: List[Attribute]
    created_at: datetime
    updated_at: datetime


# In-memory storage (replace with database in production)
listings_db: dict[UUID, Listing] = {}
search_index_db: dict[UUID, SearchIndexModel] = {}


# FastAPI Application
app = FastAPI(
    title="Item Management API",
    description="Domain-Driven Design API for Item Listing Management",
    version="1.0.0"
)


@app.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(request: CreateListingRequest):
    """Create a new listing"""
    listing = Listing(
        seller_id=request.seller_id,
        title=request.title,
        price=request.price,
        condition=request.condition,
        attributes=request.attributes or []
    )
    
    listings_db[listing.listing_id] = listing
    
    # Create search index
    search_index = SearchIndexModel(
        index_id=listing.listing_id,
        searchable_text="",
        relevance_score=0.0
    )
    search_index.update_from_listing(listing)
    search_index_db[listing.listing_id] = search_index
    
    # Publish event
    event = listing.publish_listing_indexed_event()
    
    return listing


@app.get("/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: UUID):
    """Get a listing by ID"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    return listings_db[listing_id]


@app.get("/listings", response_model=List[ListingResponse])
async def list_listings(
    seller_id: Optional[UUID] = None,
    item_state: Optional[ItemState] = None,
    skip: int = 0,
    limit: int = 100
):
    """List all listings with optional filters"""
    filtered_listings = list(listings_db.values())
    
    if seller_id:
        filtered_listings = [l for l in filtered_listings if l.seller_id == seller_id]
    
    if item_state:
        filtered_listings = [l for l in filtered_listings if l.item_state == item_state]
    
    return filtered_listings[skip:skip + limit]


@app.patch("/listings/{listing_id}/activate", response_model=ListingResponse)
async def activate_listing(listing_id: UUID):
    """Activate a listing"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    listing = listings_db[listing_id]
    try:
        listing.activate_listing()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return listing


@app.patch("/listings/{listing_id}/delist", response_model=ListingResponse)
async def delist_listing(listing_id: UUID, request: DelistRequest):
    """Delist a listing"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    listing = listings_db[listing_id]
    try:
        listing.delist_listing(request.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return listing


@app.patch("/listings/{listing_id}/price", response_model=ListingResponse)
async def update_listing_price(listing_id: UUID, request: UpdatePriceRequest):
    """Update listing price"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    listing = listings_db[listing_id]
    try:
        listing.update_price(request.new_price)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Update search index
    if listing_id in search_index_db:
        search_index_db[listing_id].update_from_listing(listing)
    
    return listing


@app.delete("/listings/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(listing_id: UUID):
    """Delete a listing"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    del listings_db[listing_id]
    if listing_id in search_index_db:
        del search_index_db[listing_id]


@app.get("/search", response_model=List[SearchIndexModel])
async def search_listings(
    query: Optional[str] = None,
    min_relevance: float = 0.0,
    skip: int = 0,
    limit: int = 100
):
    """Search listings using the search index"""
    results = list(search_index_db.values())
    
    if query:
        query_lower = query.lower()
        results = [
            r for r in results 
            if query_lower in r.searchable_text.lower()
        ]
    
    results = [r for r in results if r.relevance_score >= min_relevance]
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return results[skip:skip + limit]


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "listings_count": len(listings_db),
        "search_index_count": len(search_index_db)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
