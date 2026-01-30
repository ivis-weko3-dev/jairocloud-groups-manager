# Flask Nginx Configuration include by default.conf


# Enforces Shibboleth authentication and proxies login requests to the Flask application.
location /secure {
    limit_except GET { deny all; }
    shib_request /shibauthorizer;
    shib_request_use_headers on;

    more_clear_input_headers 'EPPN' 'DisplayName' 'JaDisplayName' 'IsMemberOf';

    uwsgi_pass unix:/run/uwsgi/app.sock;
    include uwsgi_params;

    uwsgi_param Host              $host;
    uwsgi_param X-Forwarded-For   $proxy_add_x_forwarded_for;
    uwsgi_param X-Forwarded-Proto $scheme;

    uwsgi_param SCRIPT_NAME "";
    uwsgi_param PATH_INFO "/api/auth/login";
    uwsgi_param QUERY_STRING $query_string;

    uwsgi_param HTTP_EPPN          $http_eppn;
    uwsgi_param HTTP_IsMemberOf    $http_ismemberof;
    uwsgi_param HTTP_DisplayName   $http_displayname;
    uwsgi_param HTTP_JaDisplayName $http_jadisplayname;
}
