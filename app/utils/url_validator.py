import socket
import ipaddress
from urllib.parse import urlparse
import logging


def is_safe_url(url: str) -> str | None:
    """Validates a URL to prevent SSRF and other attacks."""
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ["http", "https"]:
            return f"Invalid URL scheme: '{parsed_url.scheme}'. Only HTTP/HTTPS is allowed."
        hostname = parsed_url.hostname
        if not hostname:
            return "URL must have a valid hostname."
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            ip_str = addr_info[0][4][0]
            ip = ipaddress.ip_address(ip_str)
        except socket.gaierror as e:
            logging.exception(f"DNS resolution failed for {hostname}: {e}")
            return f"Could not resolve hostname: {hostname}"
        except Exception as e:
            logging.exception(
                f"Unexpected error during DNS resolution for {hostname}: {e}"
            )
            return "An error occurred during URL validation."
        if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
            logging.warning(f"Blocked request to unsafe IP: {ip} from URL: {url}")
            return "Access to internal or reserved IP addresses is not allowed."
    except ValueError as e:
        logging.exception(f"Invalid URL format for {url}: {e}")
        return "Invalid URL format."
    except Exception as e:
        logging.exception(f"Unexpected error during URL validation for {url}: {e}")
        return "An unexpected error occurred while validating the URL."
    return None