from peewee import Model, CharField, TextField, SqliteDatabase, DateField, FloatField, ForeignKeyField, AutoField, IntegerField

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

    class Meta:
        database = db  # Is model ka data "invoices.db" database me store hoga

# InvoiceItem model create kiya jo ek invoice ke andar items ko store karega
class InvoiceItem(Model):
    item_name = CharField(200, unique=True)  # Item ka naam, unique hoga
    qty = IntegerField()  # Item ki quantity
    rate = FloatField()  # Per unit rate
    amount = FloatField()  # Total amount (qty * rate)
    invoice = ForeignKeyField(Invoice, backref="items", lazy_load=False)  # Invoice ke sath relation

    class Meta:
        database = db  # Is model ka data "invoices.db" database me store hoga
