from app.api_endpoints import appAPI

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(appAPI, host="0.0.0.0", port=8000)
