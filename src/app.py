"""
Micro Inventory Service for AI Accountability Pipeline.
Host application used for DevSecOps lifecycle automation demo.
"""
from flask import Flask, jsonify, request


def create_app(test_config=None):
    app = Flask(__name__)
    if test_config:
        app.config.update(test_config)

    # In-memory inventory datastore
    items = [
        {"id": 1, "name": "Widget A", "quantity": 100},
        {"id": 2, "name": "Widget B", "quantity": 42},
    ]

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "service": "inventory-api",
            "version": "1.0.0",
            "status": "operational"
        }), 200

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "healthy", "service": "inventory-api"}), 200

    @app.route("/items", methods=["GET"])
    def get_items():
        return jsonify({"items": items, "count": len(items)}), 200

    @app.route("/items", methods=["POST"])
    def add_item():
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        quantity = data.get("quantity")

        if not name or not isinstance(quantity, int) or quantity < 0:
            return jsonify({
                "error": "Invalid payload. 'name' string and non-negative integer 'quantity' required."
            }), 400

        item_id = len(items) + 1
        new_item = {"id": item_id, "name": name, "quantity": quantity}
        items.append(new_item)
        return jsonify(new_item), 201

    @app.route("/ledger", methods=["GET"])
    def ledger():
        import os
        from flask import send_from_directory
        public_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
        return send_from_directory(public_dir, "index.html")

    return app


app = create_app()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
