import uuid
from datetime import datetime

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Sector(models.Model):
    """Civic issue category, e.g. Roads, Water, Power, Sanitation."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True)
    icon = models.CharField(
        max_length=50,
        default="folder",
        help_text="Lucide icon name, e.g. 'droplet', 'zap', 'trash-2'",
    )
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Department(models.Model):
    """A civic body handling one or more sectors, e.g. Nagar Nigam, Jal Sansthan."""

    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True)
    sectors = models.ManyToManyField(Sector, related_name="departments", blank=True)
    head_name = models.CharField(max_length=150, blank=True)
    head_designation = models.CharField(max_length=150, blank=True)
    contact_email = models.EmailField(blank=True)
    helpline_number = models.CharField(max_length=20, blank=True)
    emergency_number = models.CharField(max_length=20, blank=True)
    office_address = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to="departments/logos/", blank=True, null=True)
    description = models.TextField(blank=True)
    sla_hours = models.PositiveIntegerField(
        default=72, help_text="Service Level Agreement target, in hours"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class OfficerProfile(models.Model):
    """Extends a Django User as a departmental officer."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="officer_profile"
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, related_name="officers"
    )
    designation = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="officers/photos/", blank=True, null=True)
    is_active_officer = models.BooleanField(default=True)

    class Meta:
        ordering = ["user__first_name"]

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Complaint(models.Model):
    PRIORITY_CHOICES = [
        ("emergency", "Emergency"),
        ("high", "High Priority"),
        ("standard", "Standard"),
    ]
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("assigned", "Auto-Assigned"),
        ("in_progress", "Inspection / In-Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
        ("reopened", "Reopened"),
    ]

    tracking_id = models.CharField(max_length=20, unique=True, editable=False, db_index=True)

    # Citizen details
    citizen_name = models.CharField(max_length=150)
    citizen_phone = models.CharField(max_length=20)
    citizen_email = models.EmailField(blank=True)

    # Classification
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, related_name="complaints")
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints"
    )
    description = models.TextField()
    nlp_tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated keyword tags")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="standard")

    # Location
    address_text = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Evidence
    evidence_photo = models.ImageField(upload_to="complaints/evidence/", blank=True, null=True)

    # Workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    assigned_officer = models.ForeignKey(
        OfficerProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_complaints",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.tracking_id:
            self.tracking_id = self._generate_tracking_id()
        super().save(*args, **kwargs)

    def _generate_tracking_id(self):
        year = timezone.now().year
        prefix = f"CIV-{year}-"
        last = (
            Complaint.objects.filter(tracking_id__startswith=prefix)
            .order_by("-id")
            .first()
        )
        if last and last.tracking_id.startswith(prefix):
            try:
                last_num = int(last.tracking_id.replace(prefix, ""))
            except ValueError:
                last_num = 0
        else:
            last_num = 0
        return f"{prefix}{last_num + 1:04d}"

    def __str__(self):
        return self.tracking_id

    def get_absolute_url(self):
        return reverse("track_complaint") + f"?tid={self.tracking_id}"

    @property
    def is_resolved(self):
        return self.status in ("resolved", "closed")

    @property
    def progress_percent(self):
        mapping = {
            "submitted": 20,
            "assigned": 45,
            "in_progress": 70,
            "resolved": 100,
            "closed": 100,
            "reopened": 55,
        }
        return mapping.get(self.status, 0)


class ComplaintTimelineEvent(models.Model):
    """Optional granular log of status changes, shown on the tracking timeline."""

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="timeline_events")
    status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.complaint.tracking_id} -> {self.status}"


class ComplaintResolution(models.Model):
    complaint = models.OneToOneField(
        Complaint, on_delete=models.CASCADE, related_name="resolution"
    )
    remarks = models.TextField()
    proof_image = models.ImageField(upload_to="complaints/resolutions/")
    resolved_by = models.ForeignKey(
        OfficerProfile, on_delete=models.SET_NULL, null=True, related_name="resolutions"
    )
    resolved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resolution for {self.complaint.tracking_id}"


class CitizenFeedback(models.Model):
    complaint = models.OneToOneField(
        Complaint, on_delete=models.CASCADE, related_name="feedback"
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)]
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.complaint.tracking_id} - {self.rating}/5"


class StaticPage(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=160, unique=True)
    content = models.TextField(help_text="HTML or plain text content, rendered as-is")
    show_in_footer = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("page_detail", args=[self.slug])


class TeamMember(models.Model):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150, help_text="Official designation, e.g. 'Municipal Commissioner'")
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="team_members"
    )
    photo = models.ImageField(upload_to="team/photos/", blank=True, null=True)
    bio = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_ribhay_credit = models.BooleanField(
        default=False, help_text="Tick for RiBhay Studio engineering-credit entries"
    )

    class Meta:
        ordering = ["display_order", "name"]

    def __str__(self):
        return self.name
