FROM node:lts-alpine

# install simple http server for serving static content
RUN npm install -g http-server

RUN mkdir -p /frontend
# make the 'app' folder the current working directory
WORKDIR /frontend

COPY . .

WORKDIR /frontend/app

# install project dependencies
RUN npm install
# Install a lightweight web server
RUN npm install -g serve
RUN npm run build
# Set the command to run the web server
CMD ["serve", "-s", "docs"]

# Expose the port the app runs on
EXPOSE 3000
