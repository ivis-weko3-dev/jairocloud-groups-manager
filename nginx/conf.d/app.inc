# Proxy configuration for application resources

root /usr/share/nginx/html;

index index.html;

location /_nuxt/ {
  access_log off;
  log_not_found off;

  try_files $uri $uri/ /index.html;
}

location / {
  try_files $uri $uri/ /index.html;
}
