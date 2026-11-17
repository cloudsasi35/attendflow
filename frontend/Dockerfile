FROM node:20-alpine

WORKDIR /app

# Copy package files first
COPY package*.json ./

# Install dependencies
RUN npm install --verbose 2>&1 | tail -20

# Copy application
COPY . .

# Expose port
EXPOSE 5173

# Start dev server with better error handling
CMD npm run dev -- --host --port 5173
CMD ["npm", "run", "dev", "--", "--host"]
