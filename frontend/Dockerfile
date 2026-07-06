FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY . .

# NEXT_PUBLIC_* are inlined at build time. Default to same-origin ("") so the
# browser calls the ALB, which routes /agui,/conversations,/agents to the backend.
ARG NEXT_PUBLIC_BACKEND_URL=""
ARG NEXT_PUBLIC_CLIENT="custom"
ARG NEXT_PUBLIC_AUTH_MODE="dev"
ENV NEXT_PUBLIC_BACKEND_URL=$NEXT_PUBLIC_BACKEND_URL \
    NEXT_PUBLIC_CLIENT=$NEXT_PUBLIC_CLIENT \
    NEXT_PUBLIC_AUTH_MODE=$NEXT_PUBLIC_AUTH_MODE

RUN npm run build

FROM node:20-slim AS runner

ENV NODE_ENV=production

WORKDIR /app

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.mjs ./next.config.mjs

EXPOSE 3000

CMD ["npm", "run", "start"]
