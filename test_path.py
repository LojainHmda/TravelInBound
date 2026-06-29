#!/usr/bin/env python
import os
import json

# Test load_custom_payment_terms function
from app.forms.customer import load_custom_payment_terms

print("Testing load_custom_payment_terms():")
print(f"  Result: {load_custom_payment_terms()}")
print()

# Also test the path directly
print("Testing path resolution:")
customer_file_dir = os.path.dirname(os.path.abspath("app/forms/customer.py"))
print(f"  customer.py dir: {customer_file_dir}")

app_dir = os.path.dirname(customer_file_dir)
print(f"  app dir: {app_dir}")

project_root = os.path.dirname(app_dir)
print(f"  project root: {project_root}")

json_path = os.path.join(project_root, 'instance', 'global_supplier_option_values.json')
print(f"  JSON path: {json_path}")
print(f"  JSON exists: {os.path.exists(json_path)}")

if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        data = json.load(f)
    print(f"  customer_payment_terms: {data.get('customer_payment_terms', [])}")
