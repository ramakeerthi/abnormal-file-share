# Use Node.js LTS version
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install
RUN npm install -g cross-env
RUN npm install -g react-scripts

# Create certificates directory
RUN mkdir -p /app/certificates

# Copy project files
COPY . .

# Copy certificates from backend container
VOLUME /app/certificates

# Expose port 3000
EXPOSE 3000

# Start the app
CMD ["npm", "run", "start"] 