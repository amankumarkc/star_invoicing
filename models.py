from peewee import Model, CharField, TextField, SqliteDatabase, DateField, FloatField, ForeignKeyField, AutoField, IntegerField

# SQLite database ka connection banaya jo "invoices.db" naam se store hoga
db = SqliteDatabase("invoices.db")

# Customer model create kiya jo customers ki details store karega
class Customer(Model):
    full_name = CharField(200)  
    address = TextField()  

    class Meta:
        database = db  # Is model ka data "invoices.db" database me store hoga

# Invoice model create kiya jo invoices store karega
class Invoice(Model):
    invoice_id = AutoField()  
    customer = ForeignKeyField(Customer, backref="invoices")  # Customer ID jo Customer table se link hogi
    date = DateField()  
    total_amount = FloatField()  
    tax_percent = FloatField()  
    payable_amount = FloatField()  
    gov_arn = CharField(null=True)  # Added column for storing ARN

    class Meta:
        database = db  # Is model ka data "invoices.db" database me store hoga

    
# InvoiceItem model create kiya jo ek invoice ke andar items ko store karega
class InvoiceItem(Model):
    item_name = CharField(200, unique=True)  # Item ka naam, unique hoga
    qty = IntegerField()  
    rate = FloatField()  
    amount = FloatField()  
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