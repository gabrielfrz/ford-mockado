FROM node:22-alpine AS builder
WORKDIR /app
RUN npm install -g pnpm@11
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
FROM nginx:alpine
ENV PORT=4200
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /usr/local/bin/dandr-entrypoint
COPY --from=builder /app/dist/dandr-web/browser /usr/share/nginx/html
RUN chmod 0755 /usr/local/bin/dandr-entrypoint
EXPOSE 4200
ENTRYPOINT ["/usr/local/bin/dandr-entrypoint"]
