import json
from flask import Flask, render_template, request, redirect, make_response, jsonify
from peewee import SqliteDatabase
from models import Customer, Invoice, InvoiceItem, db
from weasyprint import HTML

# Flask ka ek app instance banaya
app = Flask(__name__)

# SQLite database initialize kiya
# "invoices.db" naam ka database use ho raha hai
# Tables -> Customer, Invoice, InvoiceItem

db = SqliteDatabase("invoices.db")
db.create_tables([Customer, Invoice, InvoiceItem])

# Home Page route
@app.route("/")
def home():
    recent_invoices = Invoice.select().order_by(Invoice.invoice_id.desc()).limit(5)
    return render_template("home.html", recent_invoices=recent_invoices)

# Naya customer create karne ka form return karega
@app.route("/new-customer")
def create_customer_form():
    return render_template("create-customer.html")

# Customers ke liye GET aur POST requests handle kar raha hai
@app.route("/customers", methods=["POST", "GET"])
def customers():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        address = request.form.get("address")
        Customer.create(full_name=full_name, address=address)  # Customer save kiya
        return redirect("/customers")
    
    customers = Customer.select()
    return render_template("list-customer.html", customers=customers)

# Customer edit karne ka route
@app.route("/customers/edit/<int:id>", methods=["GET", "POST"])
def edit_customer(id):
    customer = Customer.get_or_none(Customer.id == id)
    if not customer:
        return "Customer not found", 404
    
    if request.method == "POST":
        customer.full_name = request.form["full_name"]
        customer.address = request.form["address"]
        customer.save()
        return redirect("/customers")

    return render_template("edit-customer.html", customer=customer)

# Customer delete karne ka route
@app.route("/customers/delete/<int:id>", methods=["POST"])
def delete_customer(id):
    customer = Customer.get_or_none(Customer.id == id)
    if not customer:
        return "Customer not found", 404
    
    # Customer ke saath linked invoices aur unke items delete karna
    invoices = Invoice.select().where(Invoice.customer == customer)
    for invoice in invoices:
        InvoiceItem.delete().where(InvoiceItem.invoice == invoice).execute()
    Invoice.delete().where(Invoice.customer == customer).execute()
    customer.delete_instance()
    
    return redirect("/customers")

# API: Customers ka JSON return karega
@app.route("/api/customers", methods=["GET"])
def get_customers():
    customers = Customer.select()
    return jsonify([{ "id": c.id, "name": c.full_name } for c in customers])

# Naya invoice create karne ka form return karega
@app.route("/new-invoice")
def create_invoice_form():
    return render_template("create-invoice.html")

# Invoice create aur list karne ka handler
@app.route("/invoices", methods=["GET", "POST"])
def invoices():
    if request.method == "POST":
        data = request.form
        customer = Customer.get(Customer.id == data["customer"])
        tax_percent = float(data.get("tax_percent"))
        items = json.loads(data.get("invoice_items"))
        
        # Total amount calculate kiya
        total_amount = sum(int(item["qty"]) * float(item["rate"]) for item in items)
        payable_amount = total_amount + (total_amount * tax_percent) / 100
        
        # Invoice save kiya
        invoice = Invoice.create(
            customer=customer,
            date=data.get("date"),
            total_amount=total_amount,
            tax_percent=tax_percent,
            payable_amount=payable_amount,
        )
        invoice.fetch_and_store_arn()
        
        # Invoice items save kiya
        for item in items:
            InvoiceItem.create(
                invoice=invoice,
                item_name=item.get("item_name"),
                qty=item.get("qty"),
                rate=item.get("rate"),
                amount=int(item.get("qty")) * float(item.get("rate"))
            )
        
        return redirect("/invoices")
    
    return render_template("list-invoice.html", invoices=Invoice.select())

# Invoice edit karne ka route
@app.route("/invoices/edit/<int:id>", methods=["GET", "POST"])
def edit_invoice(id):
    invoice = Invoice.get_by_id(id)
    invoice_items = list(InvoiceItem.select().where(InvoiceItem.invoice == id).dicts())

    if request.method == "POST":
        data = request.form
        invoice.customer = data.get("customer")
        invoice.date = data.get("date")
        invoice.tax_percent = float(data.get("tax_percent"))
        items = json.loads(data.get("invoice_items"))
        
        total_amount = sum(int(item["qty"]) * float(item["rate"]) for item in items)
        invoice.total_amount = total_amount
        invoice.payable_amount = total_amount + (total_amount * invoice.tax_percent) / 100
        invoice.save()

        existing_items = {item.id: item for item in InvoiceItem.select().where(InvoiceItem.invoice == invoice)}
        updated_item_ids = set()

        for item in items:
            item_id = item.get("id")
            if item_id and int(item_id) in existing_items:
                existing_item = existing_items[int(item_id)]
                existing_item.item_name = item["item_name"]
                existing_item.qty = item["qty"]
                existing_item.rate = item["rate"]
                existing_item.amount = int(item["qty"]) * float(item["rate"])
                existing_item.save()
                updated_item_ids.add(int(item_id))
            else:
                new_item = InvoiceItem.create(
                    invoice=invoice,
                    item_name=item["item_name"],
                    qty=item["qty"],
                    rate=item["rate"],
                    amount=int(item["qty"]) * float(item["rate"])
                )
                updated_item_ids.add(new_item.id)

        for item_id in existing_items:
            if item_id not in updated_item_ids:
                existing_items[item_id].delete_instance()

        return redirect("/invoices")

    return render_template("edit-invoice.html", invoice=invoice, invoice_items=invoice_items)

# Invoice delete karne ka route
@app.route("/invoices/delete/<int:id>", methods=["POST"])
def delete_invoice(id):
    invoice = Invoice.get_by_id(id)
    InvoiceItem.delete().where(InvoiceItem.invoice == invoice).execute()
    invoice.delete_instance()
    return redirect("/invoices")

# Invoice PDF download karne ka route
@app.route("/download/<int:invoice_id>")
def download_pdf(invoice_id):
    invoice = Invoice.get_by_id(invoice_id)
    html = HTML(string=render_template("print/invoice.html", invoice=invoice))
    response = make_response(html.write_pdf())
    response.headers["Content-Type"] = "application/pdf"
    return response



# Reset Customer ID
# def reset_customer_ids():
#     customers = list(Customer.select().order_by(Customer.id))  # Get all customers in order
#     with db.atomic():  # Transaction for safety
#         for index, customer in enumerate(customers, start=1):
#             customer.id = index  # Assign new sequential ID
#             customer.save()
