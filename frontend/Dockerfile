# Base image for Node.js
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy the rest of the frontend code
COPY . .

# Build the Next.js application
RUN npm run build

# Expose the frontend port (default 3000)
EXPOSE 3000

# Start the Next.js server
CMD ["npm", "run", "start"]
