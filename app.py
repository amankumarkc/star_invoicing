import json

# Flask web framework import kiya for handling web requests
from flask import Flask, render_template, request, redirect, make_response, jsonify

# Peewee ORM import kiya SQLite database ko manage karne ke liye
from peewee import SqliteDatabase

# Models import kiye jo database tables ko represent karenge
from models import Customer, Invoice, InvoiceItem, db

# PDF generate karne ke liye WeasyPrint import kiya
from weasyprint import HTML


# Flask ka ek app instance banaya
app = Flask(__name__)

# SQLite database ka connection create kiya aur tables initialize kiye
# "invoices.db" naam ka database use ho raha hai
# Tables -> Customer, Invoice, InvoiceItem

db = SqliteDatabase("invoices.db")
db.create_tables([Customer, Invoice, InvoiceItem])

# Root route define kiya jo "Home Page" return karega
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
        # Form se customer ka naam aur address fetch kiya
        full_name = request.form.get("full_name")
        address = request.form.get("address")

        # Customer object create kiya aur database me save kiya
        customer = Customer(full_name=full_name, address=address)
        customer.save()
        return redirect("/customers")  # Customer list page pe redirect kiya
    else:
        # Agar GET request hai to sabhi customers ko fetch kar ke list me bheja
        customers = Customer.select()
        return render_template("list-customer.html", customers=customers)
    

@app.route("/customers/edit/<int:id>", methods=["GET", "POST"])
def edit_customer(id):
    customer = Customer.get_or_none(Customer.id == id)
    if not customer:
        return "Customer not found", 404  # Return 404 if customer doesn't exist
    
    if request.method == "POST":
        customer.full_name = request.form["full_name"]
        customer.address = request.form["address"]
        customer.save()
        return redirect("/customers")

    return render_template("edit-customer.html", customer=customer)


@app.route("/customers/delete/<int:id>", methods=["POST"])
def delete_customer(id):
    customer = Customer.get_or_none(Customer.id == id)
    if not customer:
        return "Customer not found", 404

    customer.delete_instance()
    # reset_customer_ids()  # Reset IDs after deletion
    return redirect("/customers")

@app.route("/api/customers", methods=["GET"])
def get_customers():
    """
    API Endpoint to fetch all customers from the database.

    Returns:
        JSON response containing a list of customers with their IDs and names.
    """
    # Retrieve all customer records from the database
    customers = Customer.select()

    # Convert the customer records into a list of dictionaries with 'id' and 'name'
    customer_list = [{"id": c.id, "name": c.full_name} for c in customers]

    # Return the list as a JSON response
    return jsonify(customer_list)


# Naya invoice create karne ka form return karega
@app.route("/new-invoice")
def create_invoice_form():
    return render_template("create-invoice.html")

# Invoice create aur list karne ka handler
@app.route("/invoices", methods=["GET", "POST"])
def invoices():
    if request.method == "POST":
        # Form data fetch kiya
        data = request.form
        customer = Customer.get(Customer.id == data["customer"])
        tax_percent = float(data.get("tax_percent"))

        # Invoice items ko JSON format se parse kiya
        items_json = data.get("invoice_items")
        items = json.loads(items_json)

         # Compute total amount (sum of all item amounts)
        total_amount = sum(int(item["qty"]) * float(item["rate"]) for item in items)

        # Invoice object create kiya aur database me save kiya
        invoice = Invoice(
            customer=customer,
            # customer=data.get("customer"),
            date=data.get("date"),
            total_amount=total_amount,
            tax_percent=tax_percent,
            payable_amount=total_amount + (total_amount * tax_percent) / 100,
        )
        invoice.save()

        # Generate ARN and store it
        invoice.fetch_and_store_arn()

        # Invoice items ko save kar rahe hain
        for item in items:
            InvoiceItem(
                invoice=invoice,
                item_name=item.get("item_name"),
                qty=item.get("qty"),
                rate=item.get("rate"),
                amount=int(item.get("qty")) * float(item.get("rate"))
            ).save()

        return redirect("/invoices")  # Invoice list page pe redirect kar rahe hain
    else:
        # GET request ke liye sabhi invoices ko fetch kar ke list bhej rahe hain
        return render_template("list-invoice.html", invoices=Invoice.select())
    
# Edit invoice form
@app.route("/invoices/edit/<int:id>", methods=["GET", "POST"])
def edit_invoice(id):
    invoice = Invoice.get_by_id(id)  # Fetch the invoice
    invoice_items = list(InvoiceItem.select().where(InvoiceItem.invoice == id).dicts())  # Convert to list of dicts

    if request.method == "POST":
        data = request.form
        invoice.customer = data.get("customer")
        invoice.date = data.get("date")
        invoice.tax_percent = float(data.get("tax_percent"))

        # Get updated items from form
        items_json = data.get("invoice_items")
        items = json.loads(items_json)

        # Compute new total amount
        total_amount = sum(int(item["qty"]) * float(item["rate"]) for item in items)
        invoice.total_amount = total_amount
        invoice.payable_amount = invoice.total_amount + (invoice.total_amount * invoice.tax_percent) / 100
        invoice.save()

        # Fetch existing items from DB for comparison
        existing_items = {item.id: item for item in InvoiceItem.select().where(InvoiceItem.invoice == invoice)}      

        # Track updated items
        updated_item_ids = set()

        for item in items:
            item_id = item.get("id")  # Check if item already has an ID
            if item_id and int(item_id) in existing_items:
                # Update existing item
                existing_item = existing_items[int(item_id)]
                existing_item.item_name = item["item_name"]
                existing_item.qty = item["qty"]
                existing_item.rate = item["rate"]
                existing_item.amount = int(item.get("qty")) * float(item.get("rate"))
                existing_item.save()
                updated_item_ids.add(int(item_id))
            else:
                # Create new item
                new_item = InvoiceItem.create(
                    invoice=invoice,
                    item_name=item["item_name"],
                    qty=item["qty"],
                    rate=item["rate"],
                    amount= int(item.get("qty")) * float(item.get("rate"))
                )
                updated_item_ids.add(new_item.id)

        # Delete items that were removed from the form
        for item_id in existing_items:
            if item_id not in updated_item_ids:
                existing_items[item_id].delete_instance()

        return redirect("/invoices")  # Redirect to invoice list

    return render_template("edit-invoice.html", invoice=invoice, invoice_items=invoice_items)



# Delete invoice
@app.route("/invoices/delete/<int:id>", methods=["POST"])
def delete_invoice(id):
    invoice = Invoice.get_by_id(id)
    InvoiceItem.delete().where(InvoiceItem.invoice == invoice).execute()  # Automatically delete items
    invoice.delete_instance()
    return redirect("/invoices")


# Invoice ka PDF download karne ka route
@app.route("/download/<int:invoice_id>")
def download_pdf(invoice_id):
    # Invoice ko database se fetch kiya uske ID ke basis pe
    invoice = Invoice.get_by_id(invoice_id)

    # Invoice ka HTML template render kiya aur PDF generate kiya
    html = HTML(string=render_template("print/invoice.html", invoice=invoice))
    response = make_response(html.write_pdf())

    # Response ka Content-Type PDF set kiya
    response.headers["Content-Type"] = "application/pdf"

    # User ko PDF send kiya
    return response


# Reset Customer ID
# def reset_customer_ids():
#     customers = list(Customer.select().order_by(Customer.id))  # Get all customers in order
#     with db.atomic():  # Transaction for safety
#         for index, customer in enumerate(customers, start=1):
#             customer.id = index  # Assign new sequential ID
#             customer.save()
