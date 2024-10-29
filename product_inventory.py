import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime

# Initialize the database
def initialize_db():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    # Create products table with cost price and selling price
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        sku TEXT UNIQUE,
        name TEXT,
        quantity INTEGER,
        cost_price REAL,
        selling_price REAL
    )
    ''')

    # Create sales table for tracking profit/loss
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        sku TEXT,
        quantity INTEGER,
        sale_price REAL,
        total_profit REAL,
        date TEXT
    )
    ''')
    conn.commit()
    conn.close()

# Add product to the database with cost and selling price
def add_product(sku, name, quantity, cost_price, selling_price):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO products (sku, name, quantity, cost_price, selling_price) VALUES (?, ?, ?, ?, ?)', 
                       (sku, name, quantity, cost_price, selling_price))
        conn.commit()
        messagebox.showinfo("Success", "Product added successfully!")
        update_dashboard()  # Update the dashboard after adding a product
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "SKU already exists.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add product: {e}")
    finally:
        conn.close()

# Track profit/loss after a sale
def track_sale(sku, quantity_sold):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    # Fetch product cost and quantity from the database
    cursor.execute('SELECT cost_price, selling_price, quantity FROM products WHERE sku = ?', (sku,))
    product = cursor.fetchone()

    if not product:
        messagebox.showerror("Error", "SKU does not exist.")
        return

    cost_price, selling_price, available_quantity = product
    if quantity_sold > available_quantity:
        messagebox.showerror("Error", "Not enough quantity available for sale.")
        return

    total_profit = (selling_price - cost_price) * quantity_sold  # Profit/Loss calculation

    cursor.execute('INSERT INTO sales (sku, quantity, sale_price, total_profit, date) VALUES (?, ?, ?, ?, CURRENT_DATE)', 
                   (sku, quantity_sold, selling_price, total_profit))
    
    # Update the inventory
    cursor.execute('UPDATE products SET quantity = quantity - ? WHERE sku = ?', (quantity_sold, sku))
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", f"Sale processed! Total profit: {total_profit:.2f}")
    update_profit_loss()  # Update profit and loss display

# Process a refund and update the stock and profits
def process_refund(sku, quantity_refunded):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    # Fetch product cost from the database
    cursor.execute('SELECT cost_price FROM products WHERE sku = ?', (sku,))
    product = cursor.fetchone()

    if not product:
        messagebox.showerror("Error", "SKU does not exist.")
        return

    cost_price = product[0]

    # Update the inventory (add refunded quantity back)
    cursor.execute('UPDATE products SET quantity = quantity + ? WHERE sku = ?', (quantity_refunded, sku))
    conn.commit()
    conn.close()

    messagebox.showinfo("Refund Processed", f"Refund completed for SKU: {sku}. Quantity refunded: {quantity_refunded}")

# Remove product from the database
def remove_product(sku):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM products WHERE sku = ?', (sku,))
        conn.commit()
        messagebox.showinfo("Success", "Product removed successfully!")
        update_dashboard()  # Update the dashboard after removing a product
    except Exception as e:
        messagebox.showerror("Error", f"Failed to remove product: {e}")
    finally:
        conn.close()

# Update the dashboard to display all products along with profit/loss
def update_dashboard():
    for row in tree.get_children():
        tree.delete(row)
    
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT sku, name, quantity, cost_price, selling_price FROM products')
    products = cursor.fetchall()
    conn.close()

    for product in products:
        sku, name, quantity, cost_price, selling_price = product
        total_cost = cost_price * quantity
        total_revenue = selling_price * quantity
        total_profit = total_revenue - total_cost
        tree.insert('', 'end', values=(sku, name, quantity, cost_price, selling_price, total_profit))

# Update profit and loss display
def update_profit_loss():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(total_profit) FROM sales')
    total_profit = cursor.fetchone()[0] or 0  # If None, set to 0
    cursor.close()

    profit_label.config(text=f"Total Profit: {total_profit:.2f}")

# Display low stock items
def display_low_stock():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT sku, name, quantity FROM products WHERE quantity <= ?', (5,))
    low_stock_items = cursor.fetchall()
    conn.close()

    if low_stock_items:
        alert_text = "\n".join([f"{item[1]} (SKU: {item[0]}) - {item[2]} left" for item in low_stock_items])
        messagebox.showinfo("Low Stock", alert_text)
    else:
        messagebox.showinfo("Stock Status", "All stock levels are sufficient.")

# Invoice Generation
def generate_invoice():
    invoice_window = tk.Toplevel(app)
    invoice_window.title("Invoice Generator")
    invoice_window.geometry("600x400")
    invoice_window.configure(bg="#ECDFCC")

    # Invoice Details
    tk.Label(invoice_window, text="Invoice Generator", font=('Segoe UI', 16), bg="#ECDFCC").pack(pady=10)

    tk.Label(invoice_window, text="SKU", bg="#ECDFCC").pack(pady=5)
    sku_entry = tk.Entry(invoice_window, width=30)
    sku_entry.pack(pady=5)

    tk.Label(invoice_window, text="Quantity Sold", bg="#ECDFCC").pack(pady=5)
    qty_entry = tk.Entry(invoice_window, width=30)
    qty_entry.pack(pady=5)

    tk.Label(invoice_window, text="Selling Price", bg="#ECDFCC").pack(pady=5)
    price_entry = tk.Entry(invoice_window, width=30)
    price_entry.pack(pady=5)

    def create_invoice():
        sku = sku_entry.get()
        quantity = int(qty_entry.get())
        selling_price = float(price_entry.get())
        total_amount = quantity * selling_price

        invoice_text = (
            f"Invoice\n"
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"SKU: {sku}\n"
            f"Quantity Sold: {quantity}\n"
            f"Selling Price: ${selling_price:.2f}\n"
            f"Total Amount: ${total_amount:.2f}\n"
        )

        messagebox.showinfo("Invoice", invoice_text)

    tk.Button(invoice_window, text="Generate Invoice", command=create_invoice, bg="#3C3D37", fg="white", borderwidth=2, relief="groove").pack(pady=20)

# Minimalistic UI Design
def minimalistic_ui():
    global entry_sku, entry_name, entry_quantity, entry_cost_price, entry_selling_price, tree, profit_label, app

    # Main Window
    app = tk.Tk()
    app.title("Inventory Management System")
    app.geometry('800x600')
    app.configure(bg="#ECDFCC")  # Light-themed background

    # Create a Notebook for tabs
    notebook = ttk.Notebook(app)
    notebook.pack(fill='both', expand=True)

    # Create Inventory Management Tab
    inventory_tab = tk.Frame(notebook, bg="#ECDFCC")
    notebook.add(inventory_tab, text='Inventory Management')

    # Stylish labels and buttons
    label_font = ('Segoe UI', 12)
    entry_font = ('Segoe UI', 10)
    button_style = {
        'bg': '#3C3D37', 
        'fg': 'white', 
        'font': label_font, 
        'activebackground': '#181C14', 
        'borderwidth': 2, 
        'relief': 'groove'
    }

    # SKU Label and Entry
    tk.Label(inventory_tab, text="SKU", font=label_font, bg="#ECDFCC").grid(row=0, column=0, padx=10, pady=(20, 5), sticky='w')
    entry_sku = tk.Entry(inventory_tab, font=entry_font, width=30)
    entry_sku.grid(row=0, column=1, padx=10, pady=(20, 5))

    # Product Name Label and Entry
    tk.Label(inventory_tab, text="Product Name", font=label_font, bg="#ECDFCC").grid(row=1, column=0, padx=10, pady=5, sticky='w')
    entry_name = tk.Entry(inventory_tab, font=entry_font, width=30)
    entry_name.grid(row=1, column=1, padx=10, pady=5)

    # Quantity Label and Entry
    tk.Label(inventory_tab, text="Quantity", font=label_font, bg="#ECDFCC").grid(row=2, column=0, padx=10, pady=5, sticky='w')
    entry_quantity = tk.Entry(inventory_tab, font=entry_font, width=30)
    entry_quantity.grid(row=2, column=1, padx=10, pady=5)

    # Cost Price Label and Entry
    tk.Label(inventory_tab, text="Cost Price", font=label_font, bg="#ECDFCC").grid(row=3, column=0, padx=10, pady=5, sticky='w')
    entry_cost_price = tk.Entry(inventory_tab, font=entry_font, width=30)
    entry_cost_price.grid(row=3, column=1, padx=10, pady=5)

    # Selling Price Label and Entry
    tk.Label(inventory_tab, text="Selling Price", font=label_font, bg="#ECDFCC").grid(row=4, column=0, padx=10, pady=5, sticky='w')
    entry_selling_price = tk.Entry(inventory_tab, font=entry_font, width=30)
    entry_selling_price.grid(row=4, column=1, padx=10, pady=5)

    # Buttons
    tk.Button(inventory_tab, text="Add Product", command=lambda: add_product(entry_sku.get(), entry_name.get(), int(entry_quantity.get()), float(entry_cost_price.get()), float(entry_selling_price.get())), **button_style).grid(row=5, column=0, padx=10, pady=10, sticky='ew')
    tk.Button(inventory_tab, text="Remove Product", command=lambda: remove_product(entry_sku.get()), **button_style).grid(row=5, column=1, padx=10, pady=10, sticky='ew')
    tk.Button(inventory_tab, text="Display Low Stock", command=display_low_stock, **button_style).grid(row=5, column=2, padx=10, pady=10, sticky='ew')

    # Profit and Loss Display
    profit_label = tk.Label(inventory_tab, text="Total Profit: 0.00", font=('Segoe UI', 14), bg="#ECDFCC")
    profit_label.grid(row=6, column=0, columnspan=3, pady=(20, 5))

    # Product List Display
    tree = ttk.Treeview(inventory_tab, columns=('SKU', 'Name', 'Quantity', 'Cost Price', 'Selling Price', 'Total Profit'), show='headings')
    tree.heading('SKU', text='SKU')
    tree.heading('Name', text='Name')
    tree.heading('Quantity', text='Quantity')
    tree.heading('Cost Price', text='Cost Price')
    tree.heading('Selling Price', text='Selling Price')
    tree.heading('Total Profit', text='Total Profit')
    
    # Adjust Treeview width
    tree.column('#0', width=0, stretch=tk.NO)
    tree.column('SKU', width=100, anchor='center')
    tree.column('Name', width=200, anchor='center')
    tree.column('Quantity', width=100, anchor='center')
    tree.column('Cost Price', width=100, anchor='center')
    tree.column('Selling Price', width=100, anchor='center')
    tree.column('Total Profit', width=100, anchor='center')
    
    tree.grid(row=7, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')  # Full width

    # Configure grid weights for proper resizing
    inventory_tab.grid_rowconfigure(7, weight=1)
    inventory_tab.grid_columnconfigure(0, weight=1)
    inventory_tab.grid_columnconfigure(1, weight=1)
    inventory_tab.grid_columnconfigure(2, weight=1)

    update_dashboard()  # Initial dashboard update

    # Create Invoice Tab
    invoice_tab = tk.Frame(notebook, bg="#ECDFCC")
    notebook.add(invoice_tab, text='Invoice Generator')

    # Invoice Entry Fields
    tk.Label(invoice_tab, text="SKU", bg="#ECDFCC").pack(pady=5)
    invoice_sku_entry = tk.Entry(invoice_tab, width=30)
    invoice_sku_entry.pack(pady=5)

    tk.Label(invoice_tab, text="Quantity Sold", bg="#ECDFCC").pack(pady=5)
    invoice_qty_entry = tk.Entry(invoice_tab, width=30)
    invoice_qty_entry.pack(pady=5)

    tk.Button(invoice_tab, text="Track Sale", command=lambda: track_sale(invoice_sku_entry.get(), int(invoice_qty_entry.get())), **button_style).pack(pady=10)

    tk.Button(invoice_tab, text="Generate Invoice", command=generate_invoice, **button_style).pack(pady=20)

    app.mainloop()

if __name__ == "__main__":
    initialize_db()
    minimalistic_ui()
