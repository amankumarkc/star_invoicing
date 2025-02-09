from peewee import Model, CharField, TextField, SqliteDatabase, DateField, FloatField, ForeignKeyField, AutoField, IntegerField
import requests

# SQLite database ka connection banaya jo "invoices.db" naam se store hoga
db = SqliteDatabase("invoices.db")

# Customer model create kiya jo customers ki details store karega
class Customer(Model):
    full_name = CharField(200)  # Customer ka naam, max 200 characters
    address = TextField()  # Customer ka address

    class Meta:
        database = db  # Is model ka data "invoices.db" database me store hoga

# Invoice model create kiya jo invoices store karega
class Invoice(Model):
    invoice_id = AutoField()  # Invoice ID, jo automatically increment hogi
    customer = ForeignKeyField(Customer, backref="invoices")  # Customer ID jo Customer table se link hogi
    date = DateField()  # Invoice ki date
    total_amount = FloatField()  # Total invoice amount
    tax_percent = FloatField()  # Tax ka percentage
    payable_amount = FloatField()  # Pay karne wala final amount (total + tax)
    gov_arn = CharField(null=True)  # Added column for storing ARN

    class Meta:
        database = db  # Is model ka data "invoices.db" database me store hoga

    def generate_arn(self):
        """Calls the external API to generate an ARN for the invoice."""
        url = "https://frappe.school/api/method/generate-pro-einvoice-id"
        payload = {
            "customer_name": self.customer.full_name,
            "invoice_id": self.invoice_id,
            "payable_amount": self.payable_amount
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            self.gov_arn = response.json().get("arn", "pending")
            self.save()

# InvoiceItem model create kiya jo ek invoice ke andar items ko store karega
class InvoiceItem(Model):
    item_name = CharField(200, unique=True)  # Item ka naam, unique hoga
    qty = IntegerField()  # Item ki quantity
    rate = FloatField()  # Per unit rate
    amount = FloatField()  # Total amount (qty * rate)
    invoice = ForeignKeyField(Invoice, backref="items", lazy_load=False)  # Invoice ke sath relation

    class Meta:
        database = db  # Is model ka data "invoices.db" database me store hoga

# Database tables create/update karne ke liye connection open kiya aur tables create kiye (if nahi hain) 
# Since SQLite does not support "ALTER TABLE ADD COLUMN" easily with Peewee ORM, we can manually add the column to the database using the following code:
# execute this inside your Python script:execute this inside your Python script:

# import sqlite3

# conn = sqlite3.connect("invoices.db")
# cursor = conn.cursor()
# cursor.execute("ALTER TABLE invoice ADD COLUMN gov_arn TEXT")
# conn.commit()
# conn.close()