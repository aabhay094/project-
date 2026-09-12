"""
Seeds CIVIQ with real, publicly-listed Lucknow civic-department contacts
and a broad set of grievance categories (Sectors) — so the portal works
out of the box without manual Admin data entry.

SOURCES (public official contact info, verified at time of writing):
  - Nagar Nigam Lucknow  : https://lmc.up.nic.in/helpline.aspx  (email: nnlko@nic.in, control room 1533)
  - MVVNL (Discom)       : https://uppcl.org / MVVNL customer care (email: cccmvvnl1912@gmail.com, helpline 1912)
  - UP Traffic Directorate: https://uppolice.gov.in contact page (email: dirtraffic-up@nic.in, traffic helpline 1073)
  - CMO Lucknow          : public directory listing (email: cmolko@gmail.com, phone 0522-2622080)
  - Jal Sansthan / Jalkal Vibhag is administratively part of Nagar Nigam Lucknow — no
    separate public email was found, so it shares Nagar Nigam's email below.
    Control room: 8177054003 (Jal Kal Vibhag control room).

IMPORTANT: Government contact details change over time. Verify these in
Django Admin (Department model) before relying on them for real complaints,
and update contact_email if your local ward/department has a different
current address.
"""

from django.db import migrations


def seed_data(apps, schema_editor):
    Sector = apps.get_model("civiq", "Sector")
    Department = apps.get_model("civiq", "Department")

    departments = [
        {
            "name": "Nagar Nigam Lucknow (Roads & Sanitation)",
            "slug": "nagar-nigam-lucknow",
            "head_designation": "Municipal Commissioner",
            "contact_email": "nnlko@nic.in",
            "helpline_number": "1533",
            "emergency_number": "1800-180-0522",
            "office_address": "Trilokinath Marg, Lalbagh, Lucknow - 226001, Uttar Pradesh",
            "description": (
                "Handles roads, potholes, garbage collection, street lighting, "
                "stray animals, and encroachment within Lucknow city limits."
            ),
            "sla_hours": 72,
        },
        {
            "name": "Jal Sansthan / Jalkal Vibhag, Lucknow (Water & Drainage)",
            "slug": "jal-sansthan-lucknow",
            "head_designation": "Executive Engineer, Jalkal Vibhag",
            # No separate public email found — Jalkal Vibhag is a wing of Nagar Nigam Lucknow.
            "contact_email": "nnlko@nic.in",
            "helpline_number": "8177054003",
            "emergency_number": "8177054003",
            "office_address": "Water Works Road, Aishbagh, Lucknow, Uttar Pradesh",
            "description": (
                "Handles piped water supply, water quality, sewage overflow, and "
                "drainage/waterlogging complaints in Lucknow."
            ),
            "sla_hours": 48,
        },
        {
            "name": "MVVNL — Madhyanchal Vidyut Vitran Nigam (Power / Discom)",
            "slug": "mvvnl-lucknow",
            "head_designation": "Managing Director, MVVNL",
            "contact_email": "cccmvvnl1912@gmail.com",
            "helpline_number": "1912",
            "emergency_number": "18001800440",
            "office_address": "4-A, Gokhale Marg, Lucknow, Uttar Pradesh - 226001",
            "description": (
                "Handles power outages, sparking, transformer faults, voltage "
                "issues, and electricity billing complaints across Lucknow."
            ),
            "sla_hours": 24,
        },
        {
            "name": "Traffic & Urban Mobility (UP Traffic Directorate)",
            "slug": "traffic-directorate-up",
            "head_designation": "Director, Traffic, UP Police",
            "contact_email": "dirtraffic-up@nic.in",
            "helpline_number": "1073",
            "emergency_number": "112",
            "office_address": "UP Police Headquarters, Lucknow, Uttar Pradesh",
            "description": (
                "Handles traffic signal faults, illegal parking, encroached "
                "roads, and traffic-flow complaints."
            ),
            "sla_hours": 48,
        },
        {
            "name": "Public Health Department (CMO Lucknow)",
            "slug": "public-health-lucknow",
            "head_designation": "Chief Medical Officer (CMO), Lucknow",
            "contact_email": "cmolko@gmail.com",
            "helpline_number": "05222622080",
            "emergency_number": "108",
            "office_address": "Office of the CMO, Lucknow, Uttar Pradesh",
            "description": (
                "Handles mosquito/vector-borne disease control, hospital "
                "sanitation, and public-health emergencies."
            ),
            "sla_hours": 24,
        },
    ]

    dept_objs = {}
    for d in departments:
        obj, _ = Department.objects.get_or_create(slug=d["slug"], defaults=d)
        dept_objs[d["slug"]] = obj

    sectors = [
        ("roads-potholes", "Potholes & Road Damage", "construction", "nagar-nigam-lucknow"),
        ("garbage-collection", "Garbage Collection", "trash-2", "nagar-nigam-lucknow"),
        ("street-lighting", "Street Lighting", "lightbulb", "nagar-nigam-lucknow"),
        ("stray-animals", "Stray Animals", "dog", "nagar-nigam-lucknow"),
        ("illegal-encroachment", "Illegal Encroachment", "alert-octagon", "nagar-nigam-lucknow"),
        ("water-supply", "Water Supply", "droplet", "jal-sansthan-lucknow"),
        ("sewage-drainage", "Sewage & Drainage", "waves", "jal-sansthan-lucknow"),
        ("power-outage", "Power Outage & Faults", "zap", "mvvnl-lucknow"),
        ("power-billing", "Electricity Billing", "receipt", "mvvnl-lucknow"),
        ("traffic-signal", "Traffic Signal Fault", "traffic-cone", "traffic-directorate-up"),
        ("illegal-parking", "Illegal Parking / Traffic", "car", "traffic-directorate-up"),
        ("mosquito-disease-control", "Mosquito & Disease Control", "bug", "public-health-lucknow"),
        ("hospital-sanitation", "Hospital Sanitation", "hospital", "public-health-lucknow"),
    ]

    for slug, name, icon, dept_slug in sectors:
        sector, _ = Sector.objects.get_or_create(
            slug=slug, defaults={"name": name, "icon": icon}
        )
        sector.departments.add(dept_objs[dept_slug])


def unseed_data(apps, schema_editor):
    Sector = apps.get_model("civiq", "Sector")
    Department = apps.get_model("civiq", "Department")
    slugs = [
        "roads-potholes", "garbage-collection", "street-lighting", "stray-animals",
        "illegal-encroachment", "water-supply", "sewage-drainage", "power-outage",
        "power-billing", "traffic-signal", "illegal-parking",
        "mosquito-disease-control", "hospital-sanitation",
    ]
    Sector.objects.filter(slug__in=slugs).delete()
    Department.objects.filter(
        slug__in=[
            "nagar-nigam-lucknow", "jal-sansthan-lucknow", "mvvnl-lucknow",
            "traffic-directorate-up", "public-health-lucknow",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("civiq", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]
