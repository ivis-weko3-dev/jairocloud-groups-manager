# Shibboleth Nginx Configuration include by default.conf

# Shibboleth FastCGI Authorizer
location /shibauthorizer {
  internal;
  include fastcgi_params;
  fastcgi_pass unix:/opt/shibboleth/shibauthorizer.sock;

  fastcgi_param SCRIPT_NAME /shibauthorizer;
  fastcgi_param PATH_INFO $uri;
  fastcgi_param REQUEST_METHOD $request_method;
  fastcgi_param QUERY_STRING $query_string;
  fastcgi_param SERVER_NAME $server_name;
  fastcgi_param SERVER_PORT $server_port;
  fastcgi_param SERVER_PROTOCOL $server_protocol;
}

# Shibboleth FastCGI Responder
location /shibresponder {
  internal;
  include fastcgi_params;
  fastcgi_pass unix:/opt/shibboleth/shibresponder.sock;

  fastcgi_param SCRIPT_NAME /shibresponder;
  fastcgi_param PATH_INFO $uri;
  fastcgi_param REQUEST_METHOD $request_method;
  fastcgi_param QUERY_STRING $query_string;
  fastcgi_param SERVER_NAME $server_name;
  fastcgi_param SERVER_PORT $server_port;
  fastcgi_param SERVER_PROTOCOL $server_protocol;
}

# Handling Shibboleth SSO requests
location ~ Shibboleth.sso/ {
  include fastcgi_params;
  fastcgi_pass unix:/opt/shibboleth/shibresponder.sock;
}
