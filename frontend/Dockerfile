# Stage 1: Base image
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./

# Stage 2: Development environment
FROM base AS development
# Install all dependencies (including devDependencies)
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Stage 3: Build the frontend for production
FROM base AS build
RUN npm install
COPY . .
RUN npm run build

# Stage 4: Lightweight Production environment
FROM nginx:alpine AS production
# Copy the built React/Vite assets to NGINX
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/40-env-config.sh /docker-entrypoint.d/40-env-config.sh
RUN chmod +x /docker-entrypoint.d/40-env-config.sh
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
