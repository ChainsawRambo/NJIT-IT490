FROM node:12.16.2

# Create app directory 
WORKDIR /NJIT-IT490/BACKEND

# Install everything in the app directory
COPY . /NJIT-IT490/BACKEND

# Intall npm
RUN npm install

# Run npm
CMD sh -c 'sleep 10; npm start'
