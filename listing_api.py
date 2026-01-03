"""
Item Management API - Domain-Driven Design Implementation
Based on Listing Aggregate Root from ItemManagement_ClassDiagram
"""

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timedelta
import os
import jwt
from passlib.context import CryptContext


# Security Configuration - Production Ready
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-min-32-chars-long")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


# User Models
class User(BaseModel):
    user_id: UUID = Field(default_factory=uuid4)
    username: str
    hashed_password: str
    seller_id: UUID = Field(default_factory=uuid4)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


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
users_db: dict[str, User] = {}


# Security Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user(username: str) -> Optional[User]:
    """Get user from database"""
    return users_db.get(username)


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# FastAPI Application
app = FastAPI(
    title="Item Management API",
    description="Domain-Driven Design API for Item Listing Management",
    version="1.0.0"
)


@app.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    if user_data.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    users_db[user.username] = user
    
    return {
        "message": "User registered successfully",
        "user_id": str(user.user_id),
        "seller_id": str(user.seller_id)
    }


@app.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login and get access token"""
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/listings", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    request: CreateListingRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new listing (requires authentication)"""
    # Use the authenticated user's seller_id
    listing = Listing(
        seller_id=current_user.seller_id,
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
async def activate_listing(
    listing_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Activate a listing (requires authentication)"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    listing = listings_db[listing_id]
    
    # Check if user owns this listing
    if listing.seller_id != current_user.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only activate your own listings"
        )
    
    try:
        listing.activate_listing()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return listing


@app.patch("/listings/{listing_id}/delist", response_model=ListingResponse)
async def delist_listing(
    listing_id: UUID,
    request: DelistRequest,
    current_user: User = Depends(get_current_user)
):
    """Delist a listing (requires authentication)"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    listing = listings_db[listing_id]
    
    # Check if user owns this listing
    if listing.seller_id != current_user.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delist your own listings"
        )
    
    try:
        listing.delist_listing(request.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return listing


@app.patch("/listings/{listing_id}/price", response_model=ListingResponse)
async def update_listing_price(
    listing_id: UUID,
    request: UpdatePriceRequest,
    current_user: User = Depends(get_current_user)
):
    """Update listing price (requires authentication)"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    listing = listings_db[listing_id]
    
    # Check if user owns this listing
    if listing.seller_id != current_user.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update price of your own listings"
        )
    
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
async def delete_listing(
    listing_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Delete a listing (requires authentication)"""
    if listing_id not in listings_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Listing {listing_id} not found"
        )
    
    listing = listings_db[listing_id]
    
    # Check if user owns this listing
    if listing.seller_id != current_user.seller_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own listings"
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
