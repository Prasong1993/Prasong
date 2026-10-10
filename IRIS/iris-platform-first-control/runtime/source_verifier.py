"""Fetch allowlisted HTTPS sources and verify the retrieved content digest.

This verifies source retrieval/integrity, not the semantic truth of a claim.
The raw response body is never persisted; only a digest and provenance are kept.
"""
from __future__ import annotations
import hashlib
import ipaddress
import os
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
from typing import Callable
from runtime.control_plane import ControlPlaneError

DEFAULT_HOSTS = {
    "developers.openai.com", "help.openai.com", "openai.com", "openai.github.io",
    "github.com", "raw.githubusercontent.com", "py.sdk.modelcontextprotocol.io",
    "pypi.org", "modelcontextprotocol.io",
}

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class SourceVerifier:
    def __init__(self, control, *, allowed_hosts=None, fetcher: Callable | None = None,
                 timeout_seconds: float = 8.0, max_bytes: int = 1_000_000):
        self.control = control
        configured = allowed_hosts if allowed_hosts is not None else os.environ.get("IRIS_ALLOWED_SOURCE_HOSTS", "")
        hosts = {h.strip().lower() for h in configured.split(",") if h.strip()} if isinstance(configured, str) else set(configured or ())
        self.allowed_hosts = {h.lower() for h in hosts} or set(DEFAULT_HOSTS)
        self._custom_fetcher = fetcher is not None
        self.fetcher = fetcher or self._fetch
        self.timeout_seconds = timeout_seconds
        self.max_bytes = max_bytes

    def validate_url(self, source_url: str) -> str:
        if not isinstance(source_url, str) or not source_url.strip():
            raise ControlPlaneError("SOURCE_URL_REQUIRED")
        p = urlsplit(source_url.strip())
        if p.scheme != "https" or not p.hostname or p.username or p.password:
            raise ControlPlaneError("SOURCE_URL_MUST_BE_HTTPS_WITHOUT_USERINFO")
        if p.port not in (None, 443):
            raise ControlPlaneError("SOURCE_URL_PORT_NOT_ALLOWED")
        if p.query:
            raise ControlPlaneError("SOURCE_URL_QUERY_NOT_ALLOWED")
        host = p.hostname.lower().rstrip(".")
        try:
            ipaddress.ip_address(host)
            raise ControlPlaneError("SOURCE_IP_LITERAL_NOT_ALLOWED")
        except ValueError:
            pass
        if host not in self.allowed_hosts:
            raise ControlPlaneError("SOURCE_HOST_NOT_ALLOWLISTED")
        if not self._custom_fetcher:
            try:
                addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
                for address in addresses:
                    ip = ipaddress.ip_address(address)
                    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
                        raise ControlPlaneError("SOURCE_HOST_RESOLVES_TO_NONPUBLIC_ADDRESS")
            except OSError:
                raise ControlPlaneError("SOURCE_HOST_DNS_LOOKUP_FAILED") from None
        return urlunsplit(("https", host, p.path or "/", "", ""))

    def _fetch(self, url: str):
        opener = urllib.request.build_opener(_NoRedirect())
        request = urllib.request.Request(url, headers={"User-Agent": "IRIS-EvidenceVerifier/0.1", "Accept": "text/html,text/plain,application/json,application/xml"})
        try:
            response = opener.open(request, timeout=self.timeout_seconds)
        except urllib.error.HTTPError as exc:
            if 300 <= exc.code < 400:
                raise ControlPlaneError("SOURCE_REDIRECT_REJECTED") from None
            raise ControlPlaneError(f"SOURCE_HTTP_STATUS_{exc.code}") from None
        with response:
            status = response.status
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            body = response.read(self.max_bytes + 1)
        return status, content_type, body

    def ingest(self, task_id: str, *, source_url: str, claim: str):
        normalized = None
        try:
            normalized = self.validate_url(source_url)
            status, content_type, body = self.fetcher(normalized)
            if status != 200:
                raise ControlPlaneError(f"SOURCE_HTTP_STATUS_{status}")
            if not (content_type.startswith("text/") or content_type in {"application/json", "application/xml", "application/xhtml+xml"}):
                raise ControlPlaneError("SOURCE_CONTENT_TYPE_NOT_SUPPORTED")
            if not body:
                raise ControlPlaneError("SOURCE_BODY_EMPTY")
            if len(body) > self.max_bytes:
                raise ControlPlaneError("SOURCE_BODY_TOO_LARGE")
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError:
                raise ControlPlaneError("SOURCE_BODY_NOT_UTF8") from None
            digest = hashlib.sha256(body).hexdigest()
            retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
            evidence = self.control.add_evidence(task_id, source_url=normalized, retrieved_at=retrieved_at,
                content=text, status="UNKNOWN", claim=claim)
            verified = self.control.mark_evidence_verified(evidence["evidence_id"], verifier_id="source-verifier",
                verification_ref=f"{normalized}#sha256={digest}", observed_sha256=digest)
            return {"status": "VERIFIED", "verification_scope": "SOURCE_RETRIEVAL_AND_CONTENT_DIGEST_ONLY",
                    "evidence": verified, "content_type": content_type, "content_bytes": len(body)}
        except ControlPlaneError as exc:
            try:
                host = urlsplit(source_url).hostname or "[INVALID]"
                self.control.record_verification_failure(task_id, source_host=host.lower(), reason=str(exc))
            except Exception:
                pass
            if normalized:
                try:
                    self.control.add_evidence(task_id, source_url=normalized,
                        retrieved_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        content=f"SOURCE_VERIFICATION_FAILED:{str(exc)}", status="BLOCKED",
                        claim=claim or "source verification failed")
                except Exception:
                    pass
            raise
