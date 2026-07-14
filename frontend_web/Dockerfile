FROM nginx:alpine

# Copy static frontend assets into Nginx public folder
COPY index.html /usr/share/nginx/html/
COPY index.css /usr/share/nginx/html/
COPY index.js /usr/share/nginx/html/
COPY movies/ /usr/share/nginx/html/movies/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
