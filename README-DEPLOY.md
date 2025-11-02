# Deployment Notes

- Use docker-compose-full.yml to start static site + prism mock + server stub.
- To run only the stub: cd server && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
- For payment sandbox testing, use ngrok to expose notify_url to payment providers.
