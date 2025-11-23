"""
URL Validation and Security Module

Provides secure URL validation to prevent SSRF and open redirect attacks.
Implements allowlisting, blocklisting, and validation of URLs.

Security measures:
- Domain allowlisting for external URLs
- Private IP range blocking
- Protocol validation
- URL normalization
- Hostname validation
"""

import ipaddress
import re
from typing import Optional, List, Set
from urllib.parse import urlparse, urljoin, quote
import socket
import logging

logger = logging.getLogger(__name__)


class URLSecurityError(Exception):
    """Raised when a URL fails security validation."""
    pass


class URLValidator:
    """
    Secure URL validator to prevent SSRF and open redirect vulnerabilities.

    OWASP References:
    - SSRF Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
    - Unvalidated Redirects: https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html
    """

    # Default allowed protocols
    ALLOWED_PROTOCOLS = {'http', 'https'}

    # Private IP ranges (RFC 1918, RFC 4193, etc.)
    PRIVATE_IP_RANGES = [
        ipaddress.ip_network('10.0.0.0/8'),
        ipaddress.ip_network('172.16.0.0/12'),
        ipaddress.ip_network('192.168.0.0/16'),
        ipaddress.ip_network('127.0.0.0/8'),  # Loopback
        ipaddress.ip_network('169.254.0.0/16'),  # Link-local
        ipaddress.ip_network('::1/128'),  # IPv6 loopback
        ipaddress.ip_network('fe80::/10'),  # IPv6 link-local
        ipaddress.ip_network('fc00::/7'),  # IPv6 private
    ]

    # Blocked hostnames for SSRF prevention
    BLOCKED_HOSTNAMES = {
        'localhost',
        'localhost.localdomain',
        '127.0.0.1',
        '0.0.0.0',
        '::1',
        'metadata.google.internal',  # GCP metadata
        'metadata.aws',  # AWS metadata
        '169.254.169.254',  # AWS/GCP/Azure metadata IP
    }

    # Common metadata service endpoints to block
    METADATA_ENDPOINTS = [
        '169.254.169.254',
        'metadata.google.internal',
        'metadata.aws',
        '100.100.100.200',  # Alibaba Cloud
    ]

    def __init__(
        self,
        allowed_domains: Optional[List[str]] = None,
        allowed_protocols: Optional[Set[str]] = None,
        allow_private_ips: bool = False,
        strict_mode: bool = True
    ):
        """
        Initialize URL validator.

        Args:
            allowed_domains: List of allowed domains (if None, all non-private domains allowed)
            allowed_protocols: Set of allowed protocols (default: http, https)
            allow_private_ips: Whether to allow private IP addresses (default: False)
            strict_mode: Enable strict validation (default: True)
        """
        self.allowed_domains = set(allowed_domains) if allowed_domains else None
        self.allowed_protocols = allowed_protocols or self.ALLOWED_PROTOCOLS
        self.allow_private_ips = allow_private_ips
        self.strict_mode = strict_mode

    def validate_webhook_url(self, url: str) -> str:
        """
        Validate a webhook URL to prevent SSRF attacks.

        Args:
            url: The webhook URL to validate

        Returns:
            The normalized, validated URL

        Raises:
            URLSecurityError: If the URL fails validation
        """
        if not url:
            raise URLSecurityError("URL cannot be empty")

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise URLSecurityError(f"Invalid URL format: {e}")

        # Validate protocol
        if parsed.scheme not in self.allowed_protocols:
            raise URLSecurityError(
                f"Invalid protocol '{parsed.scheme}'. "
                f"Allowed protocols: {', '.join(self.allowed_protocols)}"
            )

        # Validate hostname exists
        if not parsed.hostname:
            raise URLSecurityError("URL must have a valid hostname")

        # Check blocked hostnames
        if parsed.hostname.lower() in self.BLOCKED_HOSTNAMES:
            raise URLSecurityError(f"Hostname '{parsed.hostname}' is blocked for security reasons")

        # Check for metadata service endpoints
        if parsed.hostname in self.METADATA_ENDPOINTS:
            raise URLSecurityError(f"Access to metadata service endpoint '{parsed.hostname}' is blocked")

        # Validate against allowed domains if specified
        if self.allowed_domains:
            if not self._is_allowed_domain(parsed.hostname):
                raise URLSecurityError(
                    f"Domain '{parsed.hostname}' is not in the allowed domains list"
                )

        # Check for private IPs
        if not self.allow_private_ips:
            if self._is_private_ip(parsed.hostname):
                raise URLSecurityError(
                    f"Private IP addresses are not allowed: {parsed.hostname}"
                )

        # Additional validation for strict mode
        if self.strict_mode:
            # Check for URL encoding attacks
            if '%' in url and any(bad in url.lower() for bad in ['%00', '%0d', '%0a', '%2e%2e']):
                raise URLSecurityError("Suspicious URL encoding detected")

            # Check for unusual ports
            if parsed.port and parsed.port not in [80, 443, 8080, 8443]:
                logger.warning(f"Unusual port detected in webhook URL: {parsed.port}")

        return self._normalize_url(url)

    def validate_redirect_url(self, url: str, base_url: Optional[str] = None) -> str:
        """
        Validate a redirect URL to prevent open redirect vulnerabilities.

        Args:
            url: The redirect URL to validate
            base_url: The base URL for relative URL validation

        Returns:
            The validated URL

        Raises:
            URLSecurityError: If the URL fails validation
        """
        if not url:
            raise URLSecurityError("Redirect URL cannot be empty")

        # Handle relative URLs
        if base_url and not url.startswith(('http://', 'https://', '//')):
            # It's a relative URL, make it absolute
            url = urljoin(base_url, url)

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise URLSecurityError(f"Invalid redirect URL format: {e}")

        # Prevent protocol-relative URLs that could be exploited
        if url.startswith('//'):
            raise URLSecurityError("Protocol-relative URLs are not allowed for redirects")

        # Validate protocol
        if parsed.scheme and parsed.scheme not in self.allowed_protocols:
            raise URLSecurityError(
                f"Invalid redirect protocol '{parsed.scheme}'. "
                f"Only {', '.join(self.allowed_protocols)} are allowed"
            )

        # For absolute URLs, validate the domain
        if parsed.netloc:
            # Check if domain is allowed
            if self.allowed_domains and not self._is_allowed_domain(parsed.hostname):
                raise URLSecurityError(
                    f"Redirect to domain '{parsed.hostname}' is not allowed"
                )

            # Check for private IPs
            if not self.allow_private_ips and self._is_private_ip(parsed.hostname):
                raise URLSecurityError("Redirects to private IP addresses are not allowed")

        # Check for JavaScript URLs and data URLs
        if parsed.scheme in ['javascript', 'data', 'vbscript']:
            raise URLSecurityError(f"'{parsed.scheme}' URLs are not allowed for security reasons")

        return url

    def _is_allowed_domain(self, hostname: str) -> bool:
        """Check if hostname is in allowed domains list."""
        if not self.allowed_domains:
            return True

        hostname = hostname.lower()

        # Check exact match and subdomain match
        for allowed_domain in self.allowed_domains:
            allowed_domain = allowed_domain.lower()
            if hostname == allowed_domain or hostname.endswith(f".{allowed_domain}"):
                return True

        return False

    def _is_private_ip(self, hostname: str) -> bool:
        """Check if hostname resolves to a private IP address."""
        try:
            # Try to parse as IP address directly
            ip = ipaddress.ip_address(hostname)
            return any(ip in network for network in self.PRIVATE_IP_RANGES)
        except ValueError:
            # Not an IP address, resolve hostname
            try:
                # Resolve hostname to IP
                ip_str = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(ip_str)

                # Check if IP is in private ranges
                return any(ip in network for network in self.PRIVATE_IP_RANGES)

            except (socket.gaierror, ValueError):
                # Could not resolve hostname or invalid IP
                # In strict mode, treat unresolvable hosts as suspicious
                if self.strict_mode:
                    logger.warning(f"Could not resolve hostname: {hostname}")
                    return True  # Err on the side of caution
                return False

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent validation."""
        # Remove trailing slashes for consistency
        if url.endswith('/') and url.count('/') > 3:
            url = url.rstrip('/')

        # Ensure proper encoding of special characters
        parsed = urlparse(url)
        if parsed.path:
            # Normalize path (remove . and .. components)
            path_parts = []
            for part in parsed.path.split('/'):
                if part == '..':
                    if path_parts:
                        path_parts.pop()
                elif part and part != '.':
                    path_parts.append(part)

            normalized_path = '/' + '/'.join(path_parts) if path_parts else parsed.path

            # Reconstruct URL with normalized path
            url = f"{parsed.scheme}://{parsed.netloc}{normalized_path}"
            if parsed.query:
                url += f"?{parsed.query}"
            if parsed.fragment:
                url += f"#{parsed.fragment}"

        return url


def validate_email_tracking_redirect(url: str, allowed_domains: List[str] = None) -> str:
    """
    Validate redirect URLs for email tracking to prevent open redirects.

    Args:
        url: The URL to redirect to
        allowed_domains: List of allowed domains for redirects

    Returns:
        Validated URL

    Raises:
        URLSecurityError: If URL fails validation
    """
    # Default allowed domains for email tracking
    if not allowed_domains:
        allowed_domains = [
            'fliptechpro.com',
            'www.fliptechpro.com',
            # Add your application's domains here
        ]

    validator = URLValidator(
        allowed_domains=allowed_domains,
        allow_private_ips=False,
        strict_mode=True
    )

    return validator.validate_redirect_url(url)


def validate_webhook_endpoint(url: str, allowed_domains: List[str] = None) -> str:
    """
    Validate webhook URLs to prevent SSRF attacks.

    Args:
        url: The webhook URL to validate
        allowed_domains: List of allowed webhook domains

    Returns:
        Validated webhook URL

    Raises:
        URLSecurityError: If URL fails validation
    """
    # For webhooks, we might want to allow specific services
    if not allowed_domains:
        allowed_domains = [
            'n8n.cloud',
            'hooks.slack.com',
            'discord.com',
            'webhook.site',  # Remove in production
            # Add other trusted webhook services
        ]

    validator = URLValidator(
        allowed_domains=allowed_domains,
        allow_private_ips=False,
        strict_mode=True
    )

    return validator.validate_webhook_url(url)