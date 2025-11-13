import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Business, Pastry, Order, OrderItem

app = FastAPI(title="IZZYY'S BUSINESS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers

def to_str_id(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.get("_id"))
    doc.pop("_id", None)
    return doc

# Public endpoints

@app.get("/")
def read_root():
    return {"name": "IZZYY'S BUSINESS API", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# Business signup and approval

@app.post("/api/business/signup", response_model=dict)
async def business_signup(business: Business):
    # prevent duplicates by email
    exists = db["business"].find_one({"email": business.email}) if db else None
    if exists:
        raise HTTPException(status_code=400, detail="Business with this email already exists")
    new_id = create_document("business", business)
    return {"id": new_id, "approved": False}

class ApprovalRequest(BaseModel):
    approved: bool

@app.patch("/api/business/{business_id}/approve", response_model=dict)
async def approve_business(business_id: str, payload: ApprovalRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        res = db["business"].update_one({"_id": ObjectId(business_id)}, {"$set": {"approved": payload.approved}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Business not found")
        return {"id": business_id, "approved": payload.approved}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid business id")

@app.get("/api/business", response_model=List[dict])
async def list_businesses(only_pending: Optional[bool] = False):
    docs = get_documents("business", {"approved": False} if only_pending else {}) if db else []
    return [to_str_id(d) for d in docs]

# Pastry catalog

@app.post("/api/pastries", response_model=dict)
async def create_pastry(pastry: Pastry):
    new_id = create_document("pastry", pastry)
    return {"id": new_id}

@app.get("/api/pastries", response_model=List[dict])
async def list_pastries(active_only: Optional[bool] = True):
    docs = get_documents("pastry", {"active": True} if active_only else {}) if db else []
    return [to_str_id(d) for d in docs]

# Orders

@app.post("/api/orders", response_model=dict)
async def create_order(order: Order):
    # Verify business exists and is approved
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    b = db["business"].find_one({"_id": ObjectId(order.business_id)})
    if not b:
        raise HTTPException(status_code=404, detail="Business not found")
    if not b.get("approved", False):
        raise HTTPException(status_code=403, detail="Business not approved")

    # Optionally validate pastries exist if pastry_id provided
    for it in order.items:
        if it.pastry_id:
            try:
                p = db["pastry"].find_one({"_id": ObjectId(it.pastry_id)})
                if not p:
                    raise HTTPException(status_code=400, detail=f"Invalid pastry id: {it.pastry_id}")
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid pastry id: {it.pastry_id}")

    new_id = create_document("order", order)
    return {"id": new_id}

@app.get("/api/orders", response_model=List[dict])
async def list_orders(business_id: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    filt = {}
    if business_id:
        try:
            filt["business_id"] = business_id
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid business id")
    docs = get_documents("order", filt)
    return [to_str_id(d) for d in docs]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
