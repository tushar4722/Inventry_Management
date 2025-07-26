# app.py
# Import necessary libraries
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# --- Basic Flask App Setup ---

# Initialize the Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) to allow frontend communication
CORS(app) 

# --- Database Configuration ---

# Define the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

# Configure the SQLAlchemy database URI. We'll use SQLite for simplicity.
# The database file will be named 'inventory.db' and located in the project folder.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'inventory.db')

# Disable a feature of SQLAlchemy that we don't need and which adds overhead
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy database object
db = SQLAlchemy(app)

# --- Database Model Definition ---

# Define the Product model which corresponds to the 'product' table in the database
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    supplier = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True)

    # This is a representation method that shows how to print a Product object, useful for debugging
    def __repr__(self):
        return f'<Product {self.name}>'

    # This method converts a Product object into a dictionary, which is easily converted to JSON
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'quantity': self.quantity,
            'supplier': self.supplier,
            'category': self.category
        }

# --- API Endpoints (Routes) ---

# Endpoint to GET all products or filter them by supplier/category
@app.route('/api/products', methods=['GET'])
def get_products():
    """
    Fetches all products from the database.
    Allows filtering by 'supplier' or 'category' via query parameters.
    Example: /api/products?supplier=SupplierA
    """
    # Start with a query for all products
    query = Product.query

    # Get filter parameters from the request URL
    supplier = request.args.get('supplier')
    category = request.args.get('category')

    # Apply filters if they are provided
    if supplier:
        query = query.filter_by(supplier=supplier)
    if category:
        query = query.filter_by(category=category)
    
    # Execute the query and get all results
    products = query.all()
    
    # Convert the list of product objects to a list of dictionaries
    result = [product.to_dict() for product in products]
    
    # Return the result as a JSON response
    return jsonify(result)

# Endpoint to POST (add) a new product
@app.route('/api/products', methods=['POST'])
def add_product():
    """
    Adds a new product to the database.
    Expects a JSON payload with product details.
    """
    # Get the JSON data from the request body
    data = request.get_json()

    # Basic validation to ensure required fields are present
    if not data or not 'name' in data or not 'sku' in data or not 'quantity' in data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Create a new Product object with the provided data
    new_product = Product(
        name=data['name'],
        sku=data['sku'],
        quantity=data['quantity'],
        supplier=data.get('supplier'), # .get() is safer, returns None if key doesn't exist
        category=data.get('category')
    )

    # Add the new product to the database session and commit to save it
    db.session.add(new_product)
    db.session.commit()

    # Return the newly created product's data with a 201 Created status code
    return jsonify(new_product.to_dict()), 201

# Endpoint to PUT (update) an existing product's quantity
@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    """
    Updates an existing product, primarily for stock levels.
    """
    # Find the product by its ID, return 404 if not found
    product = Product.query.get_or_404(id)
    
    # Get the JSON data from the request body
    data = request.get_json()

    # Update the product's attributes if they are provided in the request
    if 'quantity' in data:
        product.quantity = data['quantity']
    if 'name' in data:
        product.name = data['name']
    if 'supplier' in data:
        product.supplier = data['supplier']
    if 'category' in data:
        product.category = data['category']
        
    # Commit the changes to the database
    db.session.commit()
    
    # Return the updated product's data
    return jsonify(product.to_dict())

# Endpoint to DELETE a product
@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    """
    Deletes a product from the database.
    """
    # Find the product by its ID, return 404 if not found
    product = Product.query.get_or_404(id)
    
    # Delete the product from the database
    db.session.delete(product)
    db.session.commit()
    
    # Return a success message
    return jsonify({'message': 'Product deleted successfully'})

# --- Main Execution Block ---

# This block runs only when the script is executed directly (not imported)
if __name__ == '__main__':
    # This is a one-time setup command to create the database and table
    # It checks if the database file exists before creating it.
    with app.app_context():
        if not os.path.exists(os.path.join(basedir, 'inventory.db')):
            print("Creating database and tables...")
            db.create_all()
            print("Database created successfully!")

    # Run the Flask development server
    # host='0.0.0.0' makes it accessible from other devices on the same network
    # debug=True enables auto-reloading on code changes and provides detailed error pages
    app.run(host='0.0.0.0', port=5001, debug=True)

