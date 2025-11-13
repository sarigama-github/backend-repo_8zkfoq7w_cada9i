"""
Database Schemas for IZZYY'S BUSINESS

Each Pydantic model maps to a MongoDB collection using the lowercase
of the class name as the collection name (e.g., Business -> "business").
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Business(BaseModel):
    """
    Businesses that sign up to place orders.
    Collection: "business"
    """
    name: str = Field(..., description="Business name")
    email: str = Field(..., description="Primary contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    business_type: str = Field(..., description="Type of business (restaurant, school, coffee shop, etc.)")
    address: str = Field(..., description="Primary address")
    approved: bool = Field(False, description="Whether the business has been approved to place orders")

class Pastry(BaseModel):
    """
    Pastry catalog items available to order.
    Collection: "pastry"
    """
    name: str = Field(..., description="Pastry name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Unit price")
    active: bool = Field(True, description="Whether this pastry is available")

class OrderItem(BaseModel):
    pastry_id: Optional[str] = Field(None, description="ID of pastry (optional when passing name-only)")
    name: str = Field(..., description="Pastry name at time of order")
    quantity: int = Field(..., ge=1, description="Number of units")
    unit_price: float = Field(..., ge=0, description="Unit price at time of order")

class Order(BaseModel):
    """
    Orders placed by approved businesses.
    Collection: "order"
    """
    business_id: str = Field(..., description="ID of the business placing the order")
    items: List[OrderItem] = Field(..., description="Line items")
    delivery_date: str = Field(..., description="Delivery date in ISO format (YYYY-MM-DD)")
    delivery_time: str = Field(..., description="Delivery time in 24h format (HH:MM)")
    delivery_address: str = Field(..., description="Delivery address")
    notes: Optional[str] = Field(None, description="Optional notes or instructions")
    subtotal: float = Field(..., ge=0, description="Items subtotal")
    delivery_fee: float = Field(0.0, ge=0, description="Optional delivery fee")
    total: float = Field(..., ge=0, description="Order total amount")
