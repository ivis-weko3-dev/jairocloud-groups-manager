# Proxy requests to the flask dev server

location /secure {

    proxy_pass "/api/auth/login";

    proxy_set_header Host              $host;
    proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_set_header EPPN          $http_eppn;
    proxy_set_header IsMemberOf    $http_ismemberof;
    proxy_set_header DisplayName   $http_displayname;
    proxy_set_header JaDisplayName $http_jadisplayname;

}
