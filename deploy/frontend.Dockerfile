FROM node:22-alpine AS build
WORKDIR /src
COPY frontend_vue/package.json frontend_vue/package-lock.json ./
RUN npm ci
COPY frontend_vue ./
ENV VITE_API_BASE_URL=/api
RUN npm run build

FROM caddy:2-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/dist /srv
