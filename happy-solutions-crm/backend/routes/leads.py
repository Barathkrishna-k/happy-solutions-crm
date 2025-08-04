from flask import Blueprint, request, jsonify, current_app, send_file
from bson import ObjectId
from models.lead import create_lead, update_lead, get_lead, list_leads
from models.customer import upsert_customer
from models.quote import compute_quote
from models.invoice import create_invoice, get_invoice_by_lead
from utils.pdf import generate_invoice_pdf
from utils.validators import is_object_id

import uuid
from datetime import datetime

leads_bp = Blueprint("leads", __name__)

@leads_bp.post("")
def create_new_lead():
    db = current_app.config["DB"]
    data = request.get_json() or {}
    cust_id = upsert_customer(db, data.get("customer", {}))
    payload = data.copy()
    payload["customer_id"] = cust_id
    payload["status"] = "FOLLOW_UP"
    quote = compute_quote(payload)
    payload["quote"] = quote
    lead_id = create_lead(db, payload)
    return jsonify({"message": "Lead created", "lead_id": str(lead_id)}), 201

@leads_bp.get("")
def get_all_leads():
    db = current_app.config["DB"]
    leads = list_leads(db)
    for l in leads:
        l["_id"] = str(l["_id"])
    return jsonify(leads), 200

@leads_bp.get("/<lead_id>")
def get_lead_details(lead_id):
    db = current_app.config["DB"]
    if not is_object_id(lead_id):
        return jsonify({"message": "Invalid ID"}), 400
    lead = get_lead(db, lead_id)
    if not lead:
        return jsonify({"message": "Not found"}), 404
    lead["_id"] = str(lead["_id"])
    return jsonify(lead), 200

@leads_bp.patch("/<lead_id>")
def patch_lead(lead_id):
    db = current_app.config["DB"]
    if not is_object_id(lead_id):
        return jsonify({"message": "Invalid ID"}), 400
    updates = request.get_json() or {}
    if "quote" in updates:
        updates["quote"] = compute_quote(updates)
    update_lead(db, lead_id, updates)
    return jsonify({"message": "Lead updated"}), 200

@leads_bp.post("/<lead_id>/invoice")
def create_lead_invoice(lead_id):
    db = current_app.config["DB"]
    if not is_object_id(lead_id):
        return jsonify({"message": "Invalid ID"}), 400
    lead = get_lead(db, lead_id)
    if not lead:
        return jsonify({"message": "Lead not found"}), 404
    if get_invoice_by_lead(db, lead_id):
        return jsonify({"message": "Invoice already exists"}), 400

    invoice_number = f"INV-{uuid.uuid4().hex[:6].upper()}"
    doc = {
        "lead_id": lead_id,
        "invoice_number": invoice_number,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "customer": lead.get("customer", {}),
        "charges": lead.get("quote", {}).get("charges", {}),
        "subtotal": lead.get("quote", {}).get("subtotal", 0),
        "gst": lead.get("quote", {}).get("gst", 0),
        "total": lead.get("quote", {}).get("total", 0),
    }
    create_invoice(db, doc)
    return jsonify({"message": "Invoice created", "invoice_id": str(invoice_number)}), 201

@leads_bp.get("/<lead_id>/invoice/download")
def download_invoice_pdf(lead_id):
    db = current_app.config["DB"]
    if not is_object_id(lead_id):
        return jsonify({"message": "Invalid ID"}), 400
    invoice = get_invoice_by_lead(db, lead_id)
    if not invoice:
        return jsonify({"message": "Invoice not found"}), 404
    pdf = generate_invoice_pdf(invoice)
    return send_file(
        io.BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{invoice.get('invoice_number', 'invoice')}.pdf"
    )
