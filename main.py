from fastapi import FastAPI, HTTPException, Depends
from fastapi.routing import asynccontextmanager
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlmodel import Field, SQLModel, Session, create_engine, select


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def get_session():
    """Dependency Injection provider for DB sessions (like Laravel Container binding)"""
    with Session(engine) as session:
        yield session

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: float
    sku: str = Field(unique=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    print("Database tables initialized!")
    # Everything BEFORE the yield runs on STARTUP
    yield 
    # Everything AFTER the yield runs on SHUTDOWN
    print("Application shutting down... cleaning up resources.")


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root(db: Session = Depends(get_session)):
    products = db.exec(select(Product)).all()
    print('--------------------------------')
    print(select(Product))
    print('--------------------------------')
    return {"products": products}



@app.post("/products", response_model=Product)
def create_product(product: Product, db: Session = Depends(get_session)):
    """
    Controller Action to create a product.
    
    - 'product: Product' automatically parses, validates, and blocks bad JSON.
    - 'db: Session = Depends(...)' handles our framework Dependency Injection.
    """
    # Check if SKU already exists (Like Eloquent's Product::where('sku', ...)->exists())
    statement = select(Product).where(Product.sku == product.sku)
    existing_product = db.exec(statement).first()
    
    if existing_product:
        raise HTTPException(status_code=400, detail="SKU already registered")

    # Save to database (Equivalent to $product->save() in Eloquent)
    db.add(product)
    db.commit()
    db.refresh(product) # Hydrate our object with the freshly generated primary key ID
    
    return product
