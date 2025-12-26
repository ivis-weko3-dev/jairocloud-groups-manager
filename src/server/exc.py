#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Custom exceptions for the server application."""


class JAIROCloudGroupsManagerError(Exception):
    """Base exception for the server application."""


class ServiceSettingsError(JAIROCloudGroupsManagerError):
    """Exception for service settings."""


class CredentialsError(ServiceSettingsError):
    """Exception for client credentials."""


class OAuthTokenError(ServiceSettingsError):
    """Exception for OAuth token."""
