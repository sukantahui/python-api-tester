"""
PyRestForge - SSL Certificate & Client Certificate Manager
"""

import ssl
import socket
from typing import Optional
from urllib.parse import urlparse

from src.core.models.response import SslCertificateModel
from src.utils.logger import logger


class CertManager:
    """Handles SSL context, client certificates, and remote server certificate extraction."""

    @staticmethod
    def extract_server_certificate(url: str, timeout: float = 3.0) -> Optional[SslCertificateModel]:
        """Extracts SSL/TLS certificate details from a remote HTTPS endpoint."""
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https":
            return None

        hostname = parsed.hostname
        port = parsed.port or 443

        if not hostname:
            return None

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert(binary_form=False)
                    cipher = ssock.cipher()
                    tls_version = ssock.version()

                    subject_str = ""
                    issuer_str = ""
                    valid_from = ""
                    valid_to = ""

                    if cert:
                        subject_parts = [f"{k}={v}" for item in cert.get("subject", ()) for k, v in item]
                        subject_str = ", ".join(subject_parts)

                        issuer_parts = [f"{k}={v}" for item in cert.get("issuer", ()) for k, v in item]
                        issuer_str = ", ".join(issuer_parts)

                        valid_from = cert.get("notBefore", "")
                        valid_to = cert.get("notAfter", "")

                    return SslCertificateModel(
                        subject=subject_str or hostname,
                        issuer=issuer_str or "Self-Signed or CA",
                        valid_from=valid_from,
                        valid_to=valid_to,
                        cipher=cipher[0] if cipher else "Unknown",
                        tls_version=tls_version or "TLSv1.3"
                    )
        except Exception as e:
            logger.debug(f"Could not extract SSL certificate for {url}: {e}")
            return None
