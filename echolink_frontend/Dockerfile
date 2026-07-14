# ── STAGE 1: BUILD REACT APP ──────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Copy package configuration
COPY package*.json ./

# Install npm dependencies
RUN npm ci

# Copy source code
COPY . .

# Compile and build production assets
RUN npm run build

# ── STAGE 2: SERVE VIA NGINX ──────────────────────────────────────────
FROM nginx:stable-alpine

# Copy custom Nginx config for single-page app routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled files from Stage 1
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
