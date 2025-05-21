FROM node:20-alpine AS frontend_builder
WORKDIR /home/src/frontend
COPY frontend/package*.json ./
RUN npm install --force
COPY frontend/ .
RUN npm run build


FROM python:3.12-slim-bookworm AS final_app
WORKDIR /home/src
COPY . .
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY --from=frontend_builder /home/src/frontend/dist /home/src/frontend/dist
EXPOSE 8080
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "backend.app:app"]

