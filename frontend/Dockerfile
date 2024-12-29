# Use Node.js LTS version
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install
RUN npm install -g cross-env

# Copy project files
COPY . .

# Expose port 3000
EXPOSE 3000

# Start the app with the same certificate paths as package.json
CMD ["npm", "run", "start"] 