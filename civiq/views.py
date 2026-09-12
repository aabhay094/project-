import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import (
    CitizenFeedback,
    Complaint,
    ComplaintResolution,
    ComplaintTimelineEvent,
    Department,
    OfficerProfile,
    Sector,
    StaticPage,
    TeamMember,
)
from .utils.nlp_engine import analyze_complaint, suggest_department
from .utils.notifications import send_grievance_email


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

def home(request):
    total_received = Complaint.objects.count()
    total_resolved = Complaint.objects.filter(status__in=["resolved", "closed"]).count()
    resolved_pct = round((total_resolved / total_received) * 100, 1) if total_received else 0
    active_officers = OfficerProfile.objects.filter(is_active_officer=True).count()

    sectors = Sector.objects.all()[:8]
    recent_resolutions = (
        ComplaintResolution.objects.select_related("complaint")
        .order_by("-resolved_at")[:6]
    )

    context = {
        "total_received": total_received,
        "total_resolved": total_resolved,
        "resolved_pct": resolved_pct,
        "active_officers": active_officers,
        "sectors": sectors,
        "recent_resolutions": recent_resolutions,
    }
    return render(request, "index.html", context)


def lodge_complaint(request):
    sectors = Sector.objects.all()

    if request.method == "POST":
        citizen_name = request.POST.get("citizen_name", "").strip()
        citizen_phone = request.POST.get("citizen_phone", "").strip()
        citizen_email = request.POST.get("citizen_email", "").strip()
        description = request.POST.get("description", "").strip()
        sector_id = request.POST.get("sector")
        address_text = request.POST.get("address_text", "").strip()
        latitude = request.POST.get("latitude") or None
        longitude = request.POST.get("longitude") or None
        evidence_photo = request.FILES.get("evidence_photo")

        if not (citizen_name and citizen_phone and description):
            messages.error(request, "Naam, phone number aur description bharna zaroori hai.")
            return render(request, "lodge_complaint.html", {"sectors": sectors})

        analysis = analyze_complaint(description)
        sector = None
        if sector_id:
            sector = Sector.objects.filter(id=sector_id).first()
        if sector is None and analysis["sector_slug"]:
            sector = Sector.objects.filter(slug=analysis["sector_slug"]).first()

        department = None
        if sector:
            department = sector.departments.first()

        complaint = Complaint.objects.create(
            citizen_name=citizen_name,
            citizen_phone=citizen_phone,
            citizen_email=citizen_email,
            sector=sector,
            department=department,
            description=description,
            nlp_tags=", ".join(analysis["tags"]),
            priority=analysis["priority"] if analysis["priority"] != "standard" else "standard",
            address_text=address_text,
            latitude=latitude,
            longitude=longitude,
            evidence_photo=evidence_photo,
            status="assigned" if department else "submitted",
        )
        ComplaintTimelineEvent.objects.create(
            complaint=complaint, status="submitted", note="Grievance lodged by citizen."
        )
        if department:
            ComplaintTimelineEvent.objects.create(
                complaint=complaint,
                status="assigned",
                note=f"Auto-assigned to {department.name} based on NLP analysis.",
            )
            send_grievance_email(complaint)

        messages.success(
            request,
            f"Grievance darj ho gayi hai. Aapki Tracking ID hai: {complaint.tracking_id}",
        )
        return redirect(f"/track/?tid={complaint.tracking_id}")

    return render(request, "lodge_complaint.html", {"sectors": sectors})


@require_POST
def nlp_preview(request):
    """AJAX endpoint powering the real-time NLP preview on the lodge form."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        payload = request.POST
    description = payload.get("description", "")
    analysis = analyze_complaint(description)
    department_name = suggest_department(analysis["sector_slug"])
    return JsonResponse(
        {
            "sector_slug": analysis["sector_slug"],
            "department": department_name,
            "priority": analysis["priority"],
            "tags": analysis["tags"],
            "confidence": analysis["confidence"],
        }
    )


def track_complaint(request):
    tracking_id = request.GET.get("tid", "").strip().upper()
    complaint = None
    if tracking_id:
        complaint = Complaint.objects.filter(tracking_id=tracking_id).first()
        if complaint is None:
            messages.error(request, f"'{tracking_id}' se koi grievance nahi mili.")

    if request.method == "POST" and complaint and complaint.is_resolved:
        rating = request.POST.get("rating")
        comments = request.POST.get("comments", "").strip()
        if rating and not hasattr(complaint, "feedback"):
            CitizenFeedback.objects.create(
                complaint=complaint, rating=int(rating), comments=comments
            )
            messages.success(request, "Feedback ke liye dhanyavaad!")
        return redirect(f"/track/?tid={complaint.tracking_id}")

    return render(request, "track_complaint.html", {"complaint": complaint, "tracking_id": tracking_id})


def departments(request):
    all_departments = Department.objects.prefetch_related("sectors").all()
    return render(request, "departments.html", {"departments": all_departments})


def analytics(request):
    total_received = Complaint.objects.count()
    total_resolved = Complaint.objects.filter(status__in=["resolved", "closed"]).count()
    resolved_pct = round((total_resolved / total_received) * 100, 1) if total_received else 0

    department_stats = []
    for dept in Department.objects.all():
        dept_total = Complaint.objects.filter(department=dept).count()
        dept_resolved = Complaint.objects.filter(
            department=dept, status__in=["resolved", "closed"]
        ).count()
        sla_pct = round((dept_resolved / dept_total) * 100, 1) if dept_total else 0
        department_stats.append(
            {
                "department": dept,
                "total": dept_total,
                "resolved": dept_resolved,
                "sla_pct": sla_pct,
            }
        )

    sector_breakdown = []
    for sector in Sector.objects.all():
        count = Complaint.objects.filter(sector=sector).count()
        sector_breakdown.append({"sector": sector, "count": count})
    sector_breakdown.sort(key=lambda x: x["count"], reverse=True)

    context = {
        "total_received": total_received,
        "total_resolved": total_resolved,
        "resolved_pct": resolved_pct,
        "department_stats": department_stats,
        "sector_breakdown": sector_breakdown,
    }
    return render(request, "analytics.html", context)


def team(request):
    members = TeamMember.objects.select_related("department").all()
    return render(request, "team.html", {"members": members})


def page_detail(request, slug):
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    return render(request, "page_detail.html", {"page": page})


# ---------------------------------------------------------------------------
# Officer workspace (protected)
# ---------------------------------------------------------------------------

@login_required
def officer_dashboard(request):
    profile = getattr(request.user, "officer_profile", None)
    if profile is None:
        messages.error(request, "Aapka account officer profile se linked nahi hai.")
        return redirect("home")

    queue = Complaint.objects.filter(assigned_officer=profile).order_by("-priority", "-created_at")

    tab = request.GET.get("tab", "all")
    if tab == "emergency":
        queue = queue.filter(priority="emergency")
    elif tab == "pending":
        queue = queue.filter(status__in=["submitted", "assigned"])
    elif tab == "in_progress":
        queue = queue.filter(status="in_progress")
    elif tab == "resolved":
        queue = queue.filter(status__in=["resolved", "closed"])

    counts = {
        "all": Complaint.objects.filter(assigned_officer=profile).count(),
        "emergency": Complaint.objects.filter(assigned_officer=profile, priority="emergency").count(),
        "pending": Complaint.objects.filter(
            assigned_officer=profile, status__in=["submitted", "assigned"]
        ).count(),
        "in_progress": Complaint.objects.filter(assigned_officer=profile, status="in_progress").count(),
        "resolved": Complaint.objects.filter(
            assigned_officer=profile, status__in=["resolved", "closed"]
        ).count(),
    }

    return render(
        request,
        "officer_dashboard.html",
        {"queue": queue, "active_tab": tab, "counts": counts, "profile": profile},
    )


@login_required
@require_POST
def update_complaint_status(request, tracking_id):
    profile = getattr(request.user, "officer_profile", None)
    complaint = get_object_or_404(Complaint, tracking_id=tracking_id, assigned_officer=profile)

    new_status = request.POST.get("status")
    note = request.POST.get("note", "").strip()

    if new_status in dict(Complaint.STATUS_CHOICES):
        complaint.status = new_status
        complaint.save(update_fields=["status", "updated_at"])
        ComplaintTimelineEvent.objects.create(complaint=complaint, status=new_status, note=note)

        if new_status == "resolved":
            proof_image = request.FILES.get("proof_image")
            remarks = request.POST.get("remarks", note or "Issue resolved.")
            if proof_image:
                ComplaintResolution.objects.update_or_create(
                    complaint=complaint,
                    defaults={
                        "remarks": remarks,
                        "proof_image": proof_image,
                        "resolved_by": profile,
                    },
                )
        messages.success(request, f"{tracking_id} update ho gaya: {complaint.get_status_display()}")
    else:
        messages.error(request, "Invalid status.")

    return redirect("officer_dashboard")
