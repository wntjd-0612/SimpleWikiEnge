from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

models.Base.metadata.create_all(bind=engine)

# 데이터베이스 세션을 가져오는 종속성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    pages = db.query(models.WikiPage).all()
    return templates.TemplateResponse("index.html", {"request": request, "pages": pages})

@app.get("/{title}", response_class=HTMLResponse)
async def read_page(request: Request, title: str, db: Session = Depends(get_db)):
    page = db.query(models.WikiPage).filter(models.WikiPage.title == title).first()
    if page is None:
        return templates.TemplateResponse("view.html", {"request": request, "title": title, "content": "페이지를 찾을 수 없습니다."})
    return templates.TemplateResponse("view.html", {"request": request, "title": title, "content": page.content})

@app.get("/edit/{title}", response_class=HTMLResponse)
async def edit_page(request: Request, title: str, db: Session = Depends(get_db)):
    page = db.query(models.WikiPage).filter(models.WikiPage.title == title).first()
    content = page.content if page else ""
    return templates.TemplateResponse("edit.html", {"request": request, "title": title, "content": content})

@app.post("/edit/{title}", response_class=HTMLResponse)
async def save_page(request: Request, title: str, content: str = Form(...), db: Session = Depends(get_db)):
    page = db.query(models.WikiPage).filter(models.WikiPage.title == title).first()
    if page:
        page.content = content
    else:
        page = models.WikiPage(title=title, content=content)
        db.add(page)
    db.commit()
    return templates.TemplateResponse("view.html", {"request": request, "title": title, "content": page.content})
