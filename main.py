From fastapi import FastAPI
From app.routes import routes

App = FastAPI(title="EKLESIA IA")
App.include_router(router)
