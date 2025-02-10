import requests  # HTTP requests bhejne ke liye library import kar rahe hain

def generate_arn(customer_name, invoice_id, payable_amount):
    """Invoice ke liye external API se ARN generate karne ka function"""

    url = "https://frappe.school/api/method/generate-pro-einvoice-id"  # API ka endpoint
    payload = {  
        "customer_name": customer_name,  # Customer ka naam
        "invoice_id": invoice_id,  # Invoice ka unique ID
        "payable_amount": payable_amount  # Invoice ka final amount
    }
    headers = {"Content-Type": "application/json"}  # API request ka header (JSON format specify kiya)

    try:
        response = requests.post(url, json=payload, headers=headers)  # API ko POST request bhejna
        response_data = response.json()  # Response ko JSON me convert karna

        if response.status_code == 200 and "arn" in response_data:
            return response_data["arn"]  # Agar response sahi hai, toh ARN return karo
        else:
            return "pending"  # Agar API fail ho jaye, toh "pending" return karo
            
    except requests.RequestException as e:  # Agar API request me koi error aaye
        print(f"Error generating ARN: {e}")  # Error message print karo
        return "pending"  # Network failure me bhi "pending" return karo
