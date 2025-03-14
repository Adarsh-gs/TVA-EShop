import random
import io
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from openpyxl import Workbook

def generate_otp():
    return str(random.randint(100000, 999999))

import random
import string

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_pdf(data):
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.setFont("Helvetica", 12)

    pdf_canvas.drawString(100, 800, "Sales Report")

    y = 750
    pdf_canvas.drawString(50, y, "Buyer")
    pdf_canvas.drawString(150, y, "Product Name")
    pdf_canvas.drawString(300, y, "Qty")
    pdf_canvas.drawString(350, y, "Price")
    pdf_canvas.drawString(450, y, "Total")
    y -= 20

    for row in data:
        pdf_canvas.drawString(50, y, row['buyer'])
        pdf_canvas.drawString(150, y, row['product_name'])
        pdf_canvas.drawString(300, y, str(row['quantity']))
        pdf_canvas.drawString(350, y, f"${row['price']}")
        pdf_canvas.drawString(450, y, f"${row['total']}")
        y -= 20

    pdf_canvas.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

def generate_excel(data):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sales Report"

    headers = ["Buyer", "Product Name", "Quantity", "Price", "Total"]
    sheet.append(headers)

    for row in data:
        sheet.append([row['buyer'], row['product_name'], row['quantity'], row['price'], row['total']])

    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'
    return response
