from fastapi import FastAPI

app = FastAPI()

name = "roblox"

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/account")
async def get_game(action: str):
    if action == "name":
        return name
    else:
        return "not a valid action"