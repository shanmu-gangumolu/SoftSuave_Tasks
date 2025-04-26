# GET , POST , PUT , DELETE Methods for PYTHON FastAPI

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
db = {}

class Item(BaseModel):
    name: str
    price: float
    description: str | None = None

# GET
@app.get("/items/{item_id}")
async def read_data(item_id: int):
    if item_id in db:
        return db[item_id]
    raise HTTPException(status_code=404, detail="Item not found")


# POST
@app.post("/items/{item_id}")
async def create_data(item_id: int, item: Item):
    if item_id in db:
        raise HTTPException(status_code=400, detail="Item already exists")
    db[item_id] = item.model_dump()
    return {"message": "Item created", "item": db[item_id]}


# PUT
@app.put("/items/{item_id}")
async def update_data(item_id: int, item: Item):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    db[item_id] = item.model_dump()
    return {"message": "Item updated", "item": db[item_id]}


# DELETE
@app.delete("/items/{item_id}")
async def delete_data(item_id: int):
    if item_id not in db:
        raise HTTPException(status_code=404, detail="Item not found")
    del db[item_id]
    return {"message": f"Item {item_id} was deleted"} 