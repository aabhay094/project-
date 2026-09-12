"""
CIVIQ Notifications
--------------------
Sends the lodged grievance to the assigned department's official email
address, with the citizen's photo evidence attached (if any).
"""

import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def send_grievance_email(complaint):
    """
    Emails the full grievance details to complaint.department.contact_email.
    Silently no-ops (and logs) if the department has no email configured,
    or if sending fails — this must never block the citizen's submission.
    """
    department = complaint.department
    if department is None or not department.contact_email:
        logger.warning(
            "No department/contact_email set for complaint %s — skipping email.",
            complaint.tracking_id,
        )
        return False

    subject = f"[CIVIQ] New {complaint.get_priority_display()} Grievance — {complaint.tracking_id}"

    body_lines = [
        f"A new grievance has been lodged on CIVIQ and auto-routed to {department.name}.",
        "",
        f"Tracking ID   : {complaint.tracking_id}",
        f"Sector        : {complaint.sector.name if complaint.sector else 'Unclassified'}",
        f"Priority      : {complaint.get_priority_display()}",
        f"Detected Tags : {complaint.nlp_tags or '—'}",
        "",
        f"Citizen Name  : {complaint.citizen_name}",
        f"Phone         : {complaint.citizen_phone}",
        f"Email         : {complaint.citizen_email or '—'}",
        "",
        f"Location      : {complaint.address_text or '—'}",
    ]
    if complaint.latitude and complaint.longitude:
        body_lines.append(
            f"GPS Coordinates: {complaint.latitude}, {complaint.longitude} "
            f"(https://www.google.com/maps?q={complaint.latitude},{complaint.longitude})"
        )
    body_lines += [
        "",
        "Description:",
        complaint.description,
        "",
        "— This grievance was routed automatically by CIVIQ's NLP engine.",
        "Please log in to the CIVIQ Officer Dashboard to update its status.",
    ]

    email = EmailMessage(
        subject=subject,
        body="\n".join(body_lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[department.contact_email],
    )

    if complaint.evidence_photo:
        try:
            email.attach_file(complaint.evidence_photo.path)
        except (FileNotFoundError, ValueError):
            logger.warning("Evidence photo missing on disk for %s", complaint.tracking_id)

    try:
        email.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Failed to send grievance email for %s", complaint.tracking_id)
        return False
